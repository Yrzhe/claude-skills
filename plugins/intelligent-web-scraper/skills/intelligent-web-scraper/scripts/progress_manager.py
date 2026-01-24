#!/usr/bin/env python3
"""
Progress Manager - Resume Capability for Web Scraping

Enables scraping to be resumed after interruption.
Progress is saved automatically and can be restored.

Usage:
    from progress_manager import ProgressManager

    # Start or resume a scraping task
    progress = ProgressManager("my_scrape_task")

    # Check if there's previous progress
    if progress.has_progress():
        print(f"Resuming from page {progress.current_page}")

    # During scraping
    for url in urls:
        if progress.is_completed(url):
            continue  # Skip already scraped URLs

        # Scrape the URL...
        data = scrape(url)

        # Mark as completed and save progress
        progress.mark_completed(url, data)

    # Finish the task
    progress.finish()
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

# ============================================================================
# Paths
# ============================================================================

SKILL_DIR = Path.home() / ".claude" / "skills" / "intelligent-web-scraper"
PROGRESS_DIR = SKILL_DIR / "progress"


# ============================================================================
# Progress State
# ============================================================================

@dataclass
class ProgressState:
    """Represents the state of a scraping task"""
    task_id: str
    start_url: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "in_progress"  # in_progress, completed, failed, paused

    # Progress tracking
    total_urls: int = 0
    completed_urls: int = 0
    failed_urls: int = 0
    current_page: int = 0

    # URLs tracking
    urls_to_scrape: List[str] = field(default_factory=list)
    completed_url_list: List[str] = field(default_factory=list)
    failed_url_list: List[str] = field(default_factory=list)

    # Data storage
    scraped_data: List[Dict[str, Any]] = field(default_factory=list)

    # Pagination state
    last_url: Optional[str] = None
    next_url: Optional[str] = None
    pagination_type: Optional[str] = None

    # Error tracking
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    config: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ProgressState":
        return cls(**data)


# ============================================================================
# Progress Manager
# ============================================================================

class ProgressManager:
    """
    Manages progress for a scraping task with automatic save/restore.

    Features:
    - Auto-save on each completed URL
    - Resume from last position
    - Track completed/failed URLs
    - Store scraped data incrementally
    """

    def __init__(
        self,
        task_id: Optional[str] = None,
        start_url: Optional[str] = None,
        auto_save: bool = True,
        save_interval: int = 1,  # Save after every N completions
    ):
        """
        Initialize progress manager.

        Args:
            task_id: Unique identifier for the task (auto-generated if None)
            start_url: The starting URL for the scrape
            auto_save: Whether to automatically save progress
            save_interval: How often to save (every N completions)
        """
        self.auto_save = auto_save
        self.save_interval = save_interval
        self._completions_since_save = 0

        # Create progress directory
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate or use task_id
        if task_id:
            self.task_id = task_id
        elif start_url:
            # Generate ID from URL
            url_hash = hashlib.md5(start_url.encode()).hexdigest()[:8]
            domain = urlparse(start_url).netloc.replace(".", "_")
            self.task_id = f"{domain}_{url_hash}"
        else:
            # Generate timestamp-based ID
            self.task_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.progress_file = PROGRESS_DIR / f"{self.task_id}.json"

        # Load or create state
        if self.progress_file.exists():
            self.state = self._load()
            print(f"📂 Loaded progress: {self.task_id}")
            print(f"   Status: {self.state.status}")
            print(f"   Completed: {self.state.completed_urls}/{self.state.total_urls}")
        else:
            self.state = ProgressState(
                task_id=self.task_id,
                start_url=start_url or "",
            )
            print(f"📝 New progress file: {self.task_id}")

        # Build completed URL set for fast lookup
        self._completed_set: Set[str] = set(self.state.completed_url_list)

    def _load(self) -> ProgressState:
        """Load progress from file"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ProgressState.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading progress: {e}")
            return ProgressState(task_id=self.task_id, start_url="")

    def save(self):
        """Save progress to file"""
        self.state.updated_at = datetime.now().isoformat()
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)

    def _maybe_auto_save(self):
        """Auto-save if enabled and interval reached"""
        if self.auto_save:
            self._completions_since_save += 1
            if self._completions_since_save >= self.save_interval:
                self.save()
                self._completions_since_save = 0

    # ========================================================================
    # Status Methods
    # ========================================================================

    def has_progress(self) -> bool:
        """Check if there's existing progress to resume"""
        return (
            self.state.completed_urls > 0 or
            self.state.current_page > 0 or
            len(self.state.scraped_data) > 0
        )

    def is_completed(self, url: str) -> bool:
        """Check if a URL has already been scraped"""
        return url in self._completed_set

    def is_failed(self, url: str) -> bool:
        """Check if a URL has failed"""
        return url in self.state.failed_url_list

    def get_status(self) -> Dict[str, Any]:
        """Get current progress status"""
        return {
            "task_id": self.task_id,
            "status": self.state.status,
            "progress": f"{self.state.completed_urls}/{self.state.total_urls}",
            "percent": (
                round(self.state.completed_urls / self.state.total_urls * 100, 1)
                if self.state.total_urls > 0 else 0
            ),
            "current_page": self.state.current_page,
            "failed": self.state.failed_urls,
            "last_url": self.state.last_url,
            "next_url": self.state.next_url,
            "updated_at": self.state.updated_at,
        }

    # ========================================================================
    # Progress Update Methods
    # ========================================================================

    def set_urls(self, urls: List[str]):
        """Set the list of URLs to scrape"""
        self.state.urls_to_scrape = urls
        self.state.total_urls = len(urls)
        self._maybe_auto_save()

    def add_urls(self, urls: List[str]):
        """Add more URLs to scrape"""
        for url in urls:
            if url not in self.state.urls_to_scrape:
                self.state.urls_to_scrape.append(url)
        self.state.total_urls = len(self.state.urls_to_scrape)
        self._maybe_auto_save()

    def get_remaining_urls(self) -> List[str]:
        """Get URLs that haven't been scraped yet"""
        return [
            url for url in self.state.urls_to_scrape
            if url not in self._completed_set and url not in self.state.failed_url_list
        ]

    def mark_completed(self, url: str, data: Optional[Dict[str, Any]] = None):
        """Mark a URL as successfully scraped"""
        if url not in self._completed_set:
            self._completed_set.add(url)
            self.state.completed_url_list.append(url)
            self.state.completed_urls += 1

        self.state.last_url = url
        self.state.retry_count = 0

        if data:
            # Add metadata
            data["_scraped_at"] = datetime.now().isoformat()
            data["_url"] = url
            self.state.scraped_data.append(data)

        self._maybe_auto_save()

    def mark_failed(self, url: str, error: str):
        """Mark a URL as failed"""
        if url not in self.state.failed_url_list:
            self.state.failed_url_list.append(url)
            self.state.failed_urls += 1

        self.state.last_error = error
        self.state.retry_count += 1
        self._maybe_auto_save()

    def set_current_page(self, page: int):
        """Update current page number"""
        self.state.current_page = page
        self._maybe_auto_save()

    def set_next_url(self, url: Optional[str]):
        """Set the next URL to scrape (for pagination)"""
        self.state.next_url = url
        self._maybe_auto_save()

    def set_pagination_type(self, pagination_type: str):
        """Set the detected pagination type"""
        self.state.pagination_type = pagination_type

    def set_config(self, config: Dict[str, Any]):
        """Store configuration for reference"""
        self.state.config = config

    def add_note(self, note: str):
        """Add a note to the progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state.notes += f"\n[{timestamp}] {note}"

    # ========================================================================
    # Lifecycle Methods
    # ========================================================================

    def pause(self):
        """Pause the scraping task"""
        self.state.status = "paused"
        self.add_note("Task paused")
        self.save()
        print(f"⏸️  Task paused at {self.state.completed_urls}/{self.state.total_urls}")

    def resume(self):
        """Resume the scraping task"""
        self.state.status = "in_progress"
        self.add_note("Task resumed")
        self.save()
        print(f"▶️  Resuming from {self.state.completed_urls}/{self.state.total_urls}")

    def finish(self, status: str = "completed"):
        """Mark the task as finished"""
        self.state.status = status
        self.state.updated_at = datetime.now().isoformat()
        self.add_note(f"Task {status}")
        self.save()
        print(f"✅ Task {status}: {self.state.completed_urls} URLs scraped")

    def fail(self, error: str):
        """Mark the task as failed"""
        self.state.status = "failed"
        self.state.last_error = error
        self.add_note(f"Task failed: {error}")
        self.save()
        print(f"❌ Task failed: {error}")

    def reset(self):
        """Reset progress (start fresh)"""
        self.state = ProgressState(
            task_id=self.task_id,
            start_url=self.state.start_url,
            config=self.state.config,
        )
        self._completed_set.clear()
        self.save()
        print(f"🔄 Progress reset for {self.task_id}")

    def delete(self):
        """Delete progress file"""
        if self.progress_file.exists():
            self.progress_file.unlink()
            print(f"🗑️  Deleted progress: {self.task_id}")

    # ========================================================================
    # Data Access Methods
    # ========================================================================

    def get_scraped_data(self) -> List[Dict[str, Any]]:
        """Get all scraped data"""
        return self.state.scraped_data

    def export_data(self, output_path: str, format: str = "json"):
        """Export scraped data to file"""
        data = self.get_scraped_data()

        if format == "json":
            if not output_path.endswith('.json'):
                output_path += '.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif format == "jsonl":
            if not output_path.endswith('.jsonl'):
                output_path += '.jsonl'
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"📁 Exported {len(data)} items to {output_path}")


# ============================================================================
# Utility Functions
# ============================================================================

def list_progress_files() -> List[Dict[str, Any]]:
    """List all progress files"""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    files = []
    for f in PROGRESS_DIR.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                files.append({
                    "task_id": data.get("task_id", f.stem),
                    "status": data.get("status", "unknown"),
                    "progress": f"{data.get('completed_urls', 0)}/{data.get('total_urls', 0)}",
                    "start_url": data.get("start_url", ""),
                    "updated_at": data.get("updated_at", ""),
                    "file": str(f),
                })
        except (json.JSONDecodeError, IOError):
            continue

    return sorted(files, key=lambda x: x.get("updated_at", ""), reverse=True)


def get_resumable_tasks() -> List[Dict[str, Any]]:
    """Get tasks that can be resumed"""
    return [
        f for f in list_progress_files()
        if f["status"] in ["in_progress", "paused"]
    ]


def cleanup_completed(days_old: int = 7):
    """Delete completed progress files older than N days"""
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days_old)

    for f in PROGRESS_DIR.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)

            if data.get("status") == "completed":
                updated = datetime.fromisoformat(data.get("updated_at", ""))
                if updated < cutoff:
                    f.unlink()
                    print(f"🗑️  Cleaned up: {f.name}")
        except (json.JSONDecodeError, IOError, ValueError):
            continue


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Progress Manager for Web Scraping")
    parser.add_argument("--list", "-l", action="store_true", help="List all progress files")
    parser.add_argument("--resumable", "-r", action="store_true", help="List resumable tasks")
    parser.add_argument("--status", "-s", help="Show status of a specific task")
    parser.add_argument("--delete", "-d", help="Delete a progress file")
    parser.add_argument("--cleanup", type=int, metavar="DAYS",
                        help="Clean up completed tasks older than N days")
    args = parser.parse_args()

    if args.list:
        files = list_progress_files()
        if not files:
            print("No progress files found.")
            return

        print("\n📋 Progress Files:\n")
        print(f"{'Task ID':<30} {'Status':<12} {'Progress':<12} {'Updated'}")
        print("-" * 80)
        for f in files:
            print(f"{f['task_id']:<30} {f['status']:<12} {f['progress']:<12} {f['updated_at'][:19]}")

    elif args.resumable:
        tasks = get_resumable_tasks()
        if not tasks:
            print("No resumable tasks found.")
            return

        print("\n▶️  Resumable Tasks:\n")
        for t in tasks:
            print(f"  - {t['task_id']}: {t['progress']} ({t['status']})")
            print(f"    URL: {t['start_url'][:60]}...")

    elif args.status:
        pm = ProgressManager(task_id=args.status)
        status = pm.get_status()
        print(f"\n📊 Task: {status['task_id']}\n")
        for k, v in status.items():
            print(f"  {k}: {v}")

    elif args.delete:
        pm = ProgressManager(task_id=args.delete)
        pm.delete()

    elif args.cleanup:
        cleanup_completed(args.cleanup)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
