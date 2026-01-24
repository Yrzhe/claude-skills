#!/usr/bin/env python3
"""
Concurrent Web Scraper - Parallel URL Processing

Enables scraping multiple URLs concurrently while respecting
rate limits and domain-specific constraints.

Features:
- Configurable concurrency (max parallel requests)
- Per-domain rate limiting
- Global rate limiting
- Automatic retry with exponential backoff
- Progress tracking integration
- Graceful shutdown on interrupt

Usage:
    python concurrent_scraper.py urls.txt --output results.json --concurrency 5

    # Or programmatically:
    from concurrent_scraper import ConcurrentScraper

    scraper = ConcurrentScraper(max_concurrent=5)
    results = await scraper.scrape_urls(url_list)
"""

import asyncio
import argparse
import json
import random
import signal
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

# Import progress manager
try:
    from progress_manager import ProgressManager
except ImportError:
    ProgressManager = None


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class ConcurrencyConfig:
    """Configuration for concurrent scraping"""
    # Concurrency limits
    max_concurrent: int = 5  # Max parallel requests total
    max_per_domain: int = 2  # Max parallel requests per domain

    # Rate limiting
    global_rate_limit: float = 10.0  # Max requests per second globally
    per_domain_rate_limit: float = 2.0  # Max requests per second per domain
    min_delay: float = 1.0  # Minimum delay between requests
    max_delay: float = 3.0  # Maximum delay between requests

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 5.0  # Base delay for exponential backoff
    retry_max_delay: float = 60.0  # Max retry delay

    # Timeouts
    request_timeout: int = 30000  # ms
    total_timeout: Optional[int] = None  # Total time limit for all URLs

    # Browser settings
    headless: bool = True
    user_agent: Optional[str] = None
    proxy: Optional[str] = None

    # Progress
    enable_progress: bool = True
    progress_task_id: Optional[str] = None


@dataclass
class ScrapeResult:
    """Result of scraping a single URL"""
    url: str
    success: bool
    title: str = ""
    content: str = ""
    markdown: str = ""
    error: Optional[str] = None
    status_code: Optional[int] = None
    retry_count: int = 0
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Rate Limiter
# ============================================================================

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling request rates.

    Allows bursts while maintaining average rate.
    """

    def __init__(self, rate: float, capacity: Optional[int] = None):
        """
        Args:
            rate: Tokens per second
            capacity: Maximum tokens (burst capacity), defaults to rate
        """
        self.rate = rate
        self.capacity = capacity or int(rate)
        self.tokens = float(self.capacity)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens, waiting if necessary.

        Returns: Time waited in seconds
        """
        async with self._lock:
            wait_time = 0.0

            # Refill tokens
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= tokens

            return wait_time


class DomainRateLimiter:
    """
    Per-domain rate limiting with global limit.
    """

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self.global_limiter = TokenBucketRateLimiter(config.global_rate_limit)
        self.domain_limiters: Dict[str, TokenBucketRateLimiter] = {}
        self._lock = asyncio.Lock()

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc

    async def acquire(self, url: str) -> float:
        """Acquire rate limit for URL"""
        domain = self._get_domain(url)

        # Get or create domain limiter
        async with self._lock:
            if domain not in self.domain_limiters:
                self.domain_limiters[domain] = TokenBucketRateLimiter(
                    self.config.per_domain_rate_limit
                )

        # Wait for both global and domain limits
        global_wait = await self.global_limiter.acquire()
        domain_wait = await self.domain_limiters[domain].acquire()

        # Add random jitter
        jitter = random.uniform(self.config.min_delay, self.config.max_delay)
        await asyncio.sleep(jitter)

        return global_wait + domain_wait + jitter


# ============================================================================
# Domain Semaphore Manager
# ============================================================================

class DomainSemaphoreManager:
    """
    Manages per-domain concurrency limits.
    """

    def __init__(self, max_per_domain: int):
        self.max_per_domain = max_per_domain
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, url: str):
        """Acquire semaphore for domain"""
        domain = urlparse(url).netloc

        async with self._lock:
            if domain not in self.semaphores:
                self.semaphores[domain] = asyncio.Semaphore(self.max_per_domain)

        await self.semaphores[domain].acquire()

    def release(self, url: str):
        """Release semaphore for domain"""
        domain = urlparse(url).netloc
        if domain in self.semaphores:
            self.semaphores[domain].release()


# ============================================================================
# Concurrent Scraper
# ============================================================================

class ConcurrentScraper:
    """
    Concurrent web scraper with rate limiting and progress tracking.
    """

    def __init__(self, config: Optional[ConcurrencyConfig] = None):
        self.config = config or ConcurrencyConfig()
        self.rate_limiter = DomainRateLimiter(self.config)
        self.domain_semaphores = DomainSemaphoreManager(self.config.max_per_domain)
        self.global_semaphore = asyncio.Semaphore(self.config.max_concurrent)

        # Progress tracking
        self.progress: Optional[ProgressManager] = None
        if self.config.enable_progress and ProgressManager:
            self.progress = ProgressManager(
                task_id=self.config.progress_task_id,
                auto_save=True,
                save_interval=5,
            )

        # Statistics
        self.stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "retried": 0,
            "start_time": None,
            "end_time": None,
        }

        # Shutdown flag
        self._shutdown = False
        self._active_tasks: Set[asyncio.Task] = set()

    async def _scrape_single(
        self,
        url: str,
        retry_count: int = 0,
    ) -> ScrapeResult:
        """Scrape a single URL with retry logic"""
        start_time = time.monotonic()

        # Check if already completed (for resume)
        if self.progress and self.progress.is_completed(url):
            return ScrapeResult(
                url=url,
                success=True,
                error="Already completed (skipped)",
            )

        # Check shutdown
        if self._shutdown:
            return ScrapeResult(
                url=url,
                success=False,
                error="Shutdown requested",
            )

        try:
            # Acquire rate limits
            await self.rate_limiter.acquire(url)

            # Acquire semaphores
            await self.domain_semaphores.acquire(url)
            await self.global_semaphore.acquire()

            try:
                if not CRAWL4AI_AVAILABLE:
                    return ScrapeResult(
                        url=url,
                        success=False,
                        error="Crawl4AI not installed",
                    )

                # Configure browser
                browser_config = BrowserConfig(
                    headless=self.config.headless,
                    user_agent=self.config.user_agent,
                )

                if self.config.proxy:
                    browser_config.proxy = self.config.proxy

                run_config = CrawlerRunConfig(
                    page_timeout=self.config.request_timeout,
                    wait_for="networkidle",
                )

                # Perform crawl
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result = await crawler.arun(url=url, config=run_config)

                    duration = int((time.monotonic() - start_time) * 1000)

                    if result.success:
                        scrape_result = ScrapeResult(
                            url=url,
                            success=True,
                            title=result.metadata.get('title', '') if result.metadata else '',
                            content=result.cleaned_html or '',
                            markdown=result.markdown or '',
                            retry_count=retry_count,
                            duration_ms=duration,
                        )

                        # Update progress
                        if self.progress:
                            self.progress.mark_completed(url, {
                                "title": scrape_result.title,
                                "content": scrape_result.markdown[:1000],  # Truncate for storage
                            })

                        return scrape_result
                    else:
                        raise Exception(result.error_message or "Unknown error")

            finally:
                # Release semaphores
                self.domain_semaphores.release(url)
                self.global_semaphore.release()

        except Exception as e:
            error_msg = str(e)
            duration = int((time.monotonic() - start_time) * 1000)

            # Retry logic
            if retry_count < self.config.max_retries and not self._shutdown:
                self.stats["retried"] += 1

                # Exponential backoff
                delay = min(
                    self.config.retry_base_delay * (2 ** retry_count),
                    self.config.retry_max_delay,
                )
                delay += random.uniform(0, delay * 0.1)  # Add jitter

                print(f"⚠️  Retry {retry_count + 1}/{self.config.max_retries} for {url[:50]}... (waiting {delay:.1f}s)")
                await asyncio.sleep(delay)

                return await self._scrape_single(url, retry_count + 1)

            # Mark as failed
            if self.progress:
                self.progress.mark_failed(url, error_msg)

            return ScrapeResult(
                url=url,
                success=False,
                error=error_msg,
                retry_count=retry_count,
                duration_ms=duration,
            )

    async def scrape_urls(
        self,
        urls: List[str],
        callback: Optional[Callable[[ScrapeResult], None]] = None,
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            callback: Optional callback for each completed result

        Returns:
            List of ScrapeResult objects
        """
        if not urls:
            return []

        # Initialize progress
        if self.progress:
            self.progress.set_urls(urls)
            self.progress.set_config({
                "max_concurrent": self.config.max_concurrent,
                "max_per_domain": self.config.max_per_domain,
            })

            # Get remaining URLs (for resume)
            remaining = self.progress.get_remaining_urls()
            if len(remaining) < len(urls):
                print(f"📂 Resuming: {len(urls) - len(remaining)} already completed")
                urls = remaining

        # Statistics
        self.stats["total"] = len(urls)
        self.stats["start_time"] = datetime.now().isoformat()

        print(f"\n🚀 Starting concurrent scrape:")
        print(f"   URLs: {len(urls)}")
        print(f"   Concurrency: {self.config.max_concurrent} (global), {self.config.max_per_domain} (per domain)")
        print(f"   Rate limit: {self.config.global_rate_limit}/s (global), {self.config.per_domain_rate_limit}/s (per domain)")
        print()

        results: List[ScrapeResult] = []
        results_lock = asyncio.Lock()

        async def process_url(url: str):
            """Process a single URL"""
            result = await self._scrape_single(url)

            async with results_lock:
                results.append(result)

                if result.success:
                    self.stats["completed"] += 1
                    status = "✓"
                else:
                    self.stats["failed"] += 1
                    status = "✗"

                # Progress display
                total = self.stats["total"]
                done = self.stats["completed"] + self.stats["failed"]
                print(f"[{done}/{total}] {status} {url[:60]}{'...' if len(url) > 60 else ''}")

            if callback:
                callback(result)

        # Create tasks
        tasks = [asyncio.create_task(process_url(url)) for url in urls]
        self._active_tasks = set(tasks)

        # Wait for all tasks
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            print("\n⏹️  Scraping cancelled")

        self.stats["end_time"] = datetime.now().isoformat()

        # Finish progress
        if self.progress:
            if self._shutdown:
                self.progress.pause()
            else:
                self.progress.finish()

        return results

    def request_shutdown(self):
        """Request graceful shutdown"""
        print("\n🛑 Shutdown requested, finishing current tasks...")
        self._shutdown = True

        # Cancel pending tasks
        for task in self._active_tasks:
            if not task.done():
                task.cancel()

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        stats = self.stats.copy()

        if stats["start_time"] and stats["end_time"]:
            start = datetime.fromisoformat(stats["start_time"])
            end = datetime.fromisoformat(stats["end_time"])
            duration = (end - start).total_seconds()
            stats["duration_seconds"] = duration
            stats["urls_per_second"] = (
                stats["completed"] / duration if duration > 0 else 0
            )

        return stats

    def print_summary(self):
        """Print scraping summary"""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("📊 Scraping Summary")
        print("=" * 50)
        print(f"   Total URLs: {stats['total']}")
        print(f"   Completed: {stats['completed']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Retried: {stats['retried']}")
        if "duration_seconds" in stats:
            print(f"   Duration: {stats['duration_seconds']:.1f}s")
            print(f"   Speed: {stats['urls_per_second']:.2f} URLs/s")
        print("=" * 50)


# ============================================================================
# CLI
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Concurrent Web Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape URLs from file
  python concurrent_scraper.py urls.txt --output results.json

  # High concurrency
  python concurrent_scraper.py urls.txt --concurrency 10 --per-domain 3

  # With rate limiting
  python concurrent_scraper.py urls.txt --rate-limit 5 --domain-rate-limit 1
        """
    )

    parser.add_argument("urls", help="File with URLs (one per line) or comma-separated URLs")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--concurrency", "-c", type=int, default=5,
                        help="Max concurrent requests (default: 5)")
    parser.add_argument("--per-domain", "-d", type=int, default=2,
                        help="Max concurrent per domain (default: 2)")
    parser.add_argument("--rate-limit", "-r", type=float, default=10.0,
                        help="Global rate limit (requests/second, default: 10)")
    parser.add_argument("--domain-rate-limit", type=float, default=2.0,
                        help="Per-domain rate limit (requests/second, default: 2)")
    parser.add_argument("--min-delay", type=float, default=1.0,
                        help="Min delay between requests (default: 1.0)")
    parser.add_argument("--max-delay", type=float, default=3.0,
                        help="Max delay between requests (default: 3.0)")
    parser.add_argument("--retries", type=int, default=3,
                        help="Max retries per URL (default: 3)")
    parser.add_argument("--no-progress", action="store_true",
                        help="Disable progress tracking (no resume)")
    parser.add_argument("--task-id", help="Task ID for progress tracking")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run in headless mode (default)")
    parser.add_argument("--no-headless", action="store_true",
                        help="Show browser window")

    args = parser.parse_args()

    # Load URLs
    urls = []
    if Path(args.urls).exists():
        with open(args.urls, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        urls = [u.strip() for u in args.urls.split(',') if u.strip()]

    if not urls:
        print("No URLs to scrape")
        return

    # Create config
    config = ConcurrencyConfig(
        max_concurrent=args.concurrency,
        max_per_domain=args.per_domain,
        global_rate_limit=args.rate_limit,
        per_domain_rate_limit=args.domain_rate_limit,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_retries=args.retries,
        enable_progress=not args.no_progress,
        progress_task_id=args.task_id,
        headless=not args.no_headless,
    )

    # Create scraper
    scraper = ConcurrentScraper(config)

    # Handle interrupt
    def handle_interrupt(signum, frame):
        scraper.request_shutdown()

    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)

    # Run scraping
    results = await scraper.scrape_urls(urls)

    # Print summary
    scraper.print_summary()

    # Save results
    if args.output:
        output_path = args.output
        if not output_path.endswith('.json'):
            output_path += '.json'

        data = [
            {
                "url": r.url,
                "success": r.success,
                "title": r.title,
                "content": r.markdown,
                "error": r.error,
                "duration_ms": r.duration_ms,
                "retry_count": r.retry_count,
                "timestamp": r.timestamp,
            }
            for r in results
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
