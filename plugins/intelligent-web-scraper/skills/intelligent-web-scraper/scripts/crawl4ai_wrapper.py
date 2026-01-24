#!/usr/bin/env python3
"""
Intelligent Web Scraper with Self-Learning Capabilities
Crawl4AI Wrapper for Intelligent Web Scraping

Features:
- Self-learning: Records successful patterns for reuse
- Adaptive anti-blocking: Adjusts delays based on signals
- Series discovery: Finds related articles automatically
- Multiple pagination types: Page numbers, next button, infinite scroll, load more

Usage:
    python crawl4ai_wrapper.py <url> [options]

Examples:
    python crawl4ai_wrapper.py https://example.com/products --output products.json
    python crawl4ai_wrapper.py https://blog.com/post/3 --discover-series --output series/
"""

import asyncio
import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
import fnmatch

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.extraction import JsonCssExtractionStrategy, LLMExtractionStrategy
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("⚠️ Crawl4AI not installed. Run: pip install crawl4ai && crawl4ai-setup")


# ============================================================================
# Paths
# ============================================================================

SKILL_DIR = Path.home() / ".claude" / "skills" / "intelligent-web-scraper"
EXPERIENCES_DIR = SKILL_DIR / "experiences"
PATTERNS_FILE = EXPERIENCES_DIR / "site_patterns.json"
LESSONS_FILE = EXPERIENCES_DIR / "lessons_learned.md"


# ============================================================================
# Configuration Classes
# ============================================================================

class OutputFormat(Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    CSV = "csv"
    AUTO = "auto"


@dataclass
class CrawlConfig:
    """Crawl configuration"""
    min_delay: float = 2.0
    max_delay: float = 5.0
    max_pages: int = 100
    max_retries: int = 3
    timeout: int = 30000
    headless: bool = True
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    output_format: OutputFormat = OutputFormat.AUTO
    output_path: Optional[str] = None
    discover_series: bool = False
    browser_path: Optional[str] = None


@dataclass
class SitePattern:
    """Learned pattern for a site"""
    description: str = ""
    selectors: Dict[str, Any] = field(default_factory=dict)
    pagination: Dict[str, Any] = field(default_factory=dict)
    anti_block: Dict[str, Any] = field(default_factory=dict)
    success_count: int = 0
    fail_count: int = 0
    last_success: Optional[str] = None
    last_fail: Optional[str] = None
    created_at: Optional[str] = None
    notes: str = ""
    status: str = "active"


@dataclass
class CrawlResult:
    """Crawl result"""
    url: str
    title: str
    content: str
    markdown: str
    links: List[Dict[str, str]] = field(default_factory=list)
    extracted_data: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Self-Learning System
# ============================================================================

class ExperienceManager:
    """Manages learned patterns and lessons"""

    def __init__(self):
        self.patterns: Dict = self._load_patterns()

    def _load_patterns(self) -> Dict:
        """Load patterns from file"""
        if PATTERNS_FILE.exists():
            try:
                with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"_meta": {"version": "1.0.0", "total_patterns": 0, "total_successes": 0}}

    def _save_patterns(self):
        """Save patterns to file"""
        EXPERIENCES_DIR.mkdir(parents=True, exist_ok=True)
        self.patterns["_meta"]["last_updated"] = datetime.now().isoformat()
        with open(PATTERNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)

    def _url_to_pattern(self, url: str) -> str:
        """Convert URL to pattern (replace numbers with *)"""
        parsed = urlparse(url)
        path = parsed.path

        # Replace number sequences with *
        pattern = re.sub(r'/\d+', '/*', path)
        pattern = re.sub(r'=\d+', '=*', pattern)

        return pattern

    def find_pattern(self, url: str) -> Optional[Dict]:
        """Find matching pattern for URL"""
        parsed = urlparse(url)
        domain = parsed.netloc
        url_pattern = self._url_to_pattern(url)

        if domain not in self.patterns:
            return None

        domain_patterns = self.patterns[domain].get("url_patterns", {})

        # Try exact match first
        if url_pattern in domain_patterns:
            return domain_patterns[url_pattern]

        # Try wildcard matching
        for pattern, config in domain_patterns.items():
            if fnmatch.fnmatch(url_pattern, pattern):
                return config

        return None

    def save_pattern(self, url: str, pattern_data: Dict):
        """Save or update pattern for URL"""
        parsed = urlparse(url)
        domain = parsed.netloc
        url_pattern = self._url_to_pattern(url)

        if domain not in self.patterns:
            self.patterns[domain] = {"url_patterns": {}}

        if "url_patterns" not in self.patterns[domain]:
            self.patterns[domain]["url_patterns"] = {}

        existing = self.patterns[domain]["url_patterns"].get(url_pattern, {})

        # Merge with existing
        merged = {
            "description": pattern_data.get("description", existing.get("description", "")),
            "selectors": pattern_data.get("selectors", existing.get("selectors", {})),
            "pagination": pattern_data.get("pagination", existing.get("pagination", {})),
            "anti_block": pattern_data.get("anti_block", existing.get("anti_block", {})),
            "success_count": existing.get("success_count", 0) + 1,
            "fail_count": existing.get("fail_count", 0),
            "last_success": datetime.now().isoformat(),
            "last_fail": existing.get("last_fail"),
            "created_at": existing.get("created_at", datetime.now().isoformat()),
            "notes": pattern_data.get("notes", existing.get("notes", "")),
            "status": "active"
        }

        self.patterns[domain]["url_patterns"][url_pattern] = merged
        self.patterns["_meta"]["total_patterns"] = sum(
            len(d.get("url_patterns", {}))
            for k, d in self.patterns.items() if k != "_meta"
        )
        self.patterns["_meta"]["total_successes"] = sum(
            p.get("success_count", 0)
            for k, d in self.patterns.items() if k != "_meta"
            for p in d.get("url_patterns", {}).values()
        )

        self._save_patterns()

    def record_failure(self, url: str, error: str, cause: str = "", solution: str = ""):
        """Record failure to lessons learned"""
        parsed = urlparse(url)
        domain = parsed.netloc
        url_pattern = self._url_to_pattern(url)

        # Update fail count in patterns
        if domain in self.patterns and "url_patterns" in self.patterns[domain]:
            if url_pattern in self.patterns[domain]["url_patterns"]:
                self.patterns[domain]["url_patterns"][url_pattern]["fail_count"] += 1
                self.patterns[domain]["url_patterns"][url_pattern]["last_fail"] = datetime.now().isoformat()
                self._save_patterns()

        # Append to lessons learned
        EXPERIENCES_DIR.mkdir(parents=True, exist_ok=True)

        entry = f"""
## [{datetime.now().strftime('%Y-%m-%d')}] {domain} - {url_pattern}

**Task**: Scraping {url}

**Error**:
- Type: {error}
- Details: See above

**Root Cause**: {cause or 'To be determined'}

**Resolution**: {solution or 'To be determined'}

**Tags**: #auto-logged

---
"""

        # Read existing content
        existing = ""
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
                existing = f.read()

        # Find the marker line and insert after it
        marker = "<!-- New entries go below this line -->"
        if marker in existing:
            parts = existing.split(marker)
            new_content = parts[0] + marker + entry + parts[1]
        else:
            new_content = existing + entry

        with open(LESSONS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def get_stats(self) -> Dict:
        """Get experience statistics"""
        return {
            "total_domains": len([k for k in self.patterns.keys() if k != "_meta"]),
            "total_patterns": self.patterns["_meta"].get("total_patterns", 0),
            "total_successes": self.patterns["_meta"].get("total_successes", 0),
            "last_updated": self.patterns["_meta"].get("last_updated"),
        }


# ============================================================================
# User-Agent Pool
# ============================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


# ============================================================================
# Anti-Blocking Strategy
# ============================================================================

class BlockLevel(Enum):
    NONE = 0
    LIGHT = 1
    MODERATE = 2
    SEVERE = 3


class AdaptiveRateLimiter:
    """Adaptive request rate limiter with learning"""

    def __init__(self, config: CrawlConfig, learned_config: Optional[Dict] = None):
        self.config = config
        self.block_level = BlockLevel.NONE
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.request_count = 0
        self.blocked_at = None

        # Apply learned config if available
        if learned_config:
            anti_block = learned_config.get("anti_block", {})
            self.config.min_delay = anti_block.get("min_delay", config.min_delay)
            self.config.max_delay = anti_block.get("max_delay", config.max_delay)
            self.known_block_threshold = anti_block.get("blocked_at_request")
        else:
            self.known_block_threshold = None

    def get_delay(self) -> float:
        """Get current delay"""
        multiplier = 2 ** self.block_level.value
        return random.uniform(
            self.config.min_delay * multiplier,
            self.config.max_delay * multiplier
        )

    async def wait(self):
        """Wait appropriate delay"""
        delay = self.get_delay()
        await asyncio.sleep(delay)
        self.request_count += 1

    def report_success(self):
        """Report successful request"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        if self.consecutive_successes >= 5 and self.block_level.value > 0:
            self.block_level = BlockLevel(self.block_level.value - 1)
            self.consecutive_successes = 0

    def report_failure(self, status_code: Optional[int] = None):
        """Report failed request"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        if self.blocked_at is None:
            self.blocked_at = self.request_count

        escalation = 1
        if status_code in [429, 403]:
            escalation = 2

        new_level = min(self.block_level.value + escalation, BlockLevel.SEVERE.value)
        self.block_level = BlockLevel(new_level)

    def get_learned_config(self) -> Dict:
        """Get config to save for learning"""
        return {
            "min_delay": self.config.min_delay,
            "max_delay": self.config.max_delay,
            "blocked_at_request": self.blocked_at,
        }


# ============================================================================
# Pagination Detection
# ============================================================================

def detect_pagination_type(html: str, links: List[Dict]) -> str:
    """Detect page pagination type"""
    html_lower = html.lower()

    # Check page number pagination
    pagination_indicators = ['pagination', 'page-numbers', 'pager', 'page-list']
    for indicator in pagination_indicators:
        if indicator in html_lower:
            return 'page_number'

    # Check next button
    next_indicators = ['下一页', '下一篇', 'next', 'next-page']
    for link in links:
        link_text = (link.get('text', '') or '').lower()
        link_class = (link.get('class', '') or '').lower()
        for indicator in next_indicators:
            if indicator in link_text or indicator in link_class:
                return 'next_button'

    # Check load more button
    load_more_indicators = ['load-more', 'loadmore', 'view-more', '加载更多', '查看更多']
    for indicator in load_more_indicators:
        if indicator in html_lower:
            return 'load_more'

    # Check infinite scroll
    infinite_scroll_indicators = ['infinite-scroll', 'lazy-load', 'intersection-observer']
    for indicator in infinite_scroll_indicators:
        if indicator in html_lower:
            return 'infinite_scroll'

    return 'none'


# ============================================================================
# Series Discovery
# ============================================================================

def calculate_url_similarity(url1: str, url2: str) -> float:
    """Calculate similarity between two URLs"""
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)

    if parsed1.netloc != parsed2.netloc:
        return 0.0

    path1 = parsed1.path.split('/')
    path2 = parsed2.path.split('/')

    if len(path1) != len(path2):
        return 0.3

    same = sum(1 for a, b in zip(path1, path2) if a == b)
    return same / max(len(path1), len(path2))


def extract_series_number(text: str) -> Optional[int]:
    """Extract series number from text"""
    patterns = [
        r'第\s*(\d+)\s*[章节篇部]',
        r'(part|chapter|episode)\s*(\d+)',
        r'\((\d+)/\d+\)',
        r'#(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            groups = match.groups()
            for g in groups:
                if g and g.isdigit():
                    return int(g)

    cn_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
              '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    cn_match = re.search(r'第([一二三四五六七八九十]+)[章节篇部]', text)
    if cn_match:
        return cn_map.get(cn_match.group(1))

    return None


def find_series_links(current_url: str, current_title: str, links: List[Dict]) -> List[Dict]:
    """Find potential series articles from links"""
    base_domain = urlparse(current_url).netloc
    series_candidates = []

    for link in links:
        url = link.get('href', '')
        text = link.get('text', '')

        if not url:
            continue

        if not url.startswith('http'):
            url = urljoin(current_url, url)

        if urlparse(url).netloc != base_domain:
            continue

        if url == current_url:
            continue

        score = 0

        url_sim = calculate_url_similarity(url, current_url)
        score += url_sim * 30

        series_indicators = ['prev', 'next', '上一', '下一', 'previous', 'following',
                             '目录', 'contents', 'index', 'series', '系列']
        for indicator in series_indicators:
            if indicator in text.lower() or indicator in url.lower():
                score += 20
                break

        if re.search(r'\d+', url):
            score += 10

        if current_title and text:
            current_clean = re.sub(r'\d+', '', current_title.lower())
            text_clean = re.sub(r'\d+', '', text.lower())
            if current_clean and text_clean:
                common = len(set(current_clean) & set(text_clean))
                score += min(common, 10)

        if score >= 30:
            series_candidates.append({
                'url': url,
                'text': text,
                'score': score,
                'series_number': extract_series_number(text) or extract_series_number(url)
            })

    series_candidates.sort(key=lambda x: x['score'], reverse=True)
    return series_candidates


# ============================================================================
# Main Crawler Class
# ============================================================================

class IntelligentCrawler:
    """Intelligent web crawler with self-learning"""

    def __init__(self, config: CrawlConfig):
        self.config = config
        self.experience = ExperienceManager()
        self.visited_urls = set()
        self.results: List[CrawlResult] = []
        self.learned_pattern = None

        # Show experience stats
        stats = self.experience.get_stats()
        if stats["total_patterns"] > 0:
            print(f"📚 Experience loaded: {stats['total_domains']} domains, "
                  f"{stats['total_patterns']} patterns, {stats['total_successes']} successes")

    def _check_experience(self, url: str) -> Optional[Dict]:
        """Check if we have experience with this URL pattern"""
        pattern = self.experience.find_pattern(url)
        if pattern:
            print(f"✨ Found learned pattern for this URL (used {pattern.get('success_count', 0)} times)")
            if pattern.get('notes'):
                print(f"   Note: {pattern['notes']}")
            self.learned_pattern = pattern
        return pattern

    async def crawl_single(self, url: str) -> CrawlResult:
        """Crawl single page"""
        if not CRAWL4AI_AVAILABLE:
            return CrawlResult(
                url=url,
                title="",
                content="",
                markdown="",
                success=False,
                error="Crawl4AI not installed"
            )

        # Check for learned pattern
        learned = self._check_experience(url) if not self.learned_pattern else self.learned_pattern

        # Initialize rate limiter with learned config
        rate_limiter = AdaptiveRateLimiter(self.config, learned)

        browser_config = BrowserConfig(
            headless=self.config.headless,
            user_agent=self.config.user_agent or get_random_user_agent(),
        )

        if self.config.browser_path:
            browser_config.executable_path = self.config.browser_path

        if self.config.proxy:
            browser_config.proxy = self.config.proxy

        run_config = CrawlerRunConfig(
            page_timeout=self.config.timeout,
            wait_for="networkidle",
        )

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)

                if result.success:
                    rate_limiter.report_success()

                    links = []
                    if result.links:
                        for link in result.links.get('internal', []):
                            links.append({
                                'href': link.get('href', ''),
                                'text': link.get('text', ''),
                            })

                    crawl_result = CrawlResult(
                        url=url,
                        title=result.metadata.get('title', '') if result.metadata else '',
                        content=result.cleaned_html or '',
                        markdown=result.markdown or '',
                        links=links,
                        extracted_data=result.extracted_content,
                        success=True,
                    )

                    # Save learned pattern on success
                    self.experience.save_pattern(url, {
                        "description": f"Auto-learned from {url}",
                        "pagination": {"type": detect_pagination_type(crawl_result.content, links)},
                        "anti_block": rate_limiter.get_learned_config(),
                        "notes": "",
                    })

                    return crawl_result
                else:
                    rate_limiter.report_failure()
                    self.experience.record_failure(url, result.error_message or "Unknown error")
                    return CrawlResult(
                        url=url,
                        title="",
                        content="",
                        markdown="",
                        success=False,
                        error=result.error_message,
                    )

        except Exception as e:
            rate_limiter.report_failure()
            self.experience.record_failure(url, str(e))
            return CrawlResult(
                url=url,
                title="",
                content="",
                markdown="",
                success=False,
                error=str(e),
            )

    async def crawl_with_pagination(self, start_url: str) -> List[CrawlResult]:
        """Crawl with pagination handling"""
        results = []
        current_url = start_url
        page_count = 0

        # Check for learned pattern
        learned = self._check_experience(start_url)
        rate_limiter = AdaptiveRateLimiter(self.config, learned)

        while current_url and page_count < self.config.max_pages:
            if current_url in self.visited_urls:
                break

            self.visited_urls.add(current_url)

            print(f"📄 Crawling page {page_count + 1}: {current_url}")

            result = await self.crawl_single(current_url)
            results.append(result)
            page_count += 1

            if not result.success:
                print(f"❌ Failed: {result.error}")
                break

            pagination_type = detect_pagination_type(result.content, result.links)

            if pagination_type == 'none':
                break

            # Find next page
            next_url = None
            next_patterns = ['next', '下一页', '下一篇', '»', '→']

            for link in result.links:
                link_text = (link.get('text', '') or '').lower()
                for pattern in next_patterns:
                    if pattern in link_text:
                        next_url = link.get('href')
                        if next_url and not next_url.startswith('http'):
                            next_url = urljoin(current_url, next_url)
                        break
                if next_url:
                    break

            if not next_url or next_url == current_url:
                break

            current_url = next_url
            await rate_limiter.wait()

        return results

    async def discover_and_crawl_series(self, start_url: str) -> List[CrawlResult]:
        """Discover and crawl article series"""
        print(f"🔍 Analyzing series: {start_url}")

        first_result = await self.crawl_single(start_url)
        if not first_result.success:
            return [first_result]

        self.visited_urls.add(start_url)

        series_links = find_series_links(
            start_url,
            first_result.title,
            first_result.links
        )

        if not series_links:
            print("ℹ️ No series links found")
            return [first_result]

        print(f"✅ Found {len(series_links)} potential series links")

        all_results = [first_result]
        urls_to_crawl = [link['url'] for link in series_links[:self.config.max_pages - 1]]

        learned = self._check_experience(start_url)
        rate_limiter = AdaptiveRateLimiter(self.config, learned)

        for i, url in enumerate(urls_to_crawl):
            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)

            print(f"📄 Crawling ({i + 2}/{len(urls_to_crawl) + 1}): {url}")

            result = await self.crawl_single(url)
            all_results.append(result)

            if not result.success:
                print(f"⚠️ Failed: {result.error}")

            await rate_limiter.wait()

        # Sort by series number
        def get_order(r):
            num = extract_series_number(r.title) or extract_series_number(r.url)
            return num if num else 999

        all_results.sort(key=get_order)

        return all_results


# ============================================================================
# Output Handling
# ============================================================================

def save_results(results: List[CrawlResult], config: CrawlConfig):
    """Save crawl results"""
    if not results:
        print("⚠️ No results to save")
        return

    output_path = config.output_path or f"crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_format = config.output_format
    if output_format == OutputFormat.AUTO:
        if len(results) > 1 and all(len(r.markdown) > 500 for r in results if r.success):
            output_format = OutputFormat.MARKDOWN
        else:
            output_format = OutputFormat.JSON

    if output_format == OutputFormat.JSON:
        if not output_path.endswith('.json'):
            output_path += '.json'

        data = [
            {
                'url': r.url,
                'title': r.title,
                'content': r.markdown,
                'success': r.success,
                'error': r.error,
                'timestamp': r.timestamp,
            }
            for r in results
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved to {output_path} ({len(results)} records)")

    elif output_format == OutputFormat.MARKDOWN:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, result in enumerate(results, 1):
            if not result.success:
                continue

            title = result.title or f"article_{i}"
            safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:50]
            filename = f"{i:02d}_{safe_title}.md"

            filepath = output_dir / filename

            content = f"# {result.title}\n\n"
            content += f"> Source: {result.url}\n\n"
            content += result.markdown

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        print(f"✅ Saved to {output_dir}/ ({len([r for r in results if r.success])} files)")

    elif output_format == OutputFormat.CSV:
        import csv

        if not output_path.endswith('.csv'):
            output_path += '.csv'

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Title', 'Success', 'Error', 'Timestamp'])
            for r in results:
                writer.writerow([r.url, r.title, r.success, r.error or '', r.timestamp])

        print(f"✅ Saved to {output_path} ({len(results)} records)")


# ============================================================================
# CLI Entry Point
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description='Intelligent Web Scraper with Self-Learning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawl4ai_wrapper.py https://example.com/products
  python crawl4ai_wrapper.py https://blog.com/post --discover-series
  python crawl4ai_wrapper.py https://shop.com --output products.json --format json
        """
    )

    parser.add_argument('url', help='URL to crawl')
    parser.add_argument('--output', '-o', help='Output path')
    parser.add_argument('--format', '-f', choices=['json', 'markdown', 'csv', 'auto'],
                        default='auto', help='Output format (default: auto)')
    parser.add_argument('--discover-series', '-s', action='store_true',
                        help='Discover and crawl article series')
    parser.add_argument('--max-pages', type=int, default=100,
                        help='Maximum pages to crawl (default: 100)')
    parser.add_argument('--min-delay', type=float, default=2.0,
                        help='Minimum delay in seconds (default: 2.0)')
    parser.add_argument('--max-delay', type=float, default=5.0,
                        help='Maximum delay in seconds (default: 5.0)')
    parser.add_argument('--proxy', help='Proxy server (format: http://host:port)')
    parser.add_argument('--no-headless', action='store_true',
                        help='Show browser window')
    parser.add_argument('--browser-path', help='Custom browser path')
    parser.add_argument('--stats', action='store_true',
                        help='Show experience statistics and exit')

    args = parser.parse_args()

    # Show stats if requested
    if args.stats:
        exp = ExperienceManager()
        stats = exp.get_stats()
        print("\n📊 Experience Statistics:")
        print(f"   Domains learned: {stats['total_domains']}")
        print(f"   URL patterns: {stats['total_patterns']}")
        print(f"   Total successes: {stats['total_successes']}")
        print(f"   Last updated: {stats['last_updated'] or 'Never'}")
        return

    config = CrawlConfig(
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_pages=args.max_pages,
        headless=not args.no_headless,
        proxy=args.proxy,
        output_format=OutputFormat(args.format),
        output_path=args.output,
        discover_series=args.discover_series,
        browser_path=args.browser_path,
    )

    crawler = IntelligentCrawler(config)

    print(f"\n🚀 Starting crawl: {args.url}")
    print(f"   Max pages: {config.max_pages}")
    print(f"   Delay range: {config.min_delay}-{config.max_delay}s")
    print()

    if config.discover_series:
        results = await crawler.discover_and_crawl_series(args.url)
    else:
        results = await crawler.crawl_with_pagination(args.url)

    print()
    print(f"📊 Complete: {len(results)} pages, {len([r for r in results if r.success])} successful")

    save_results(results, config)


if __name__ == '__main__':
    asyncio.run(main())
