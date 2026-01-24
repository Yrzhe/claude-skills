#!/usr/bin/env python3
"""
Configuration Manager for Intelligent Web Scraper

Handles environment detection and configuration for both
local (GUI) and VPS (headless) environments.

Usage:
    from config import get_config, is_headless

    config = get_config()
    if is_headless():
        # Use headless-specific settings
        pass
"""

import os
import platform
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

# ============================================================================
# Paths
# ============================================================================

SKILL_DIR = Path.home() / ".claude" / "skills" / "intelligent-web-scraper"
CONFIG_FILE = SKILL_DIR / "config.json"
EXPERIENCES_DIR = SKILL_DIR / "experiences"
PATTERNS_FILE = EXPERIENCES_DIR / "site_patterns.json"
LESSONS_FILE = EXPERIENCES_DIR / "lessons_learned.md"


# ============================================================================
# Environment Detection
# ============================================================================

def detect_os() -> str:
    """Detect operating system"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    return "unknown"


def is_headless() -> bool:
    """
    Detect if running in a headless (no GUI) environment.

    Returns True if:
    - No DISPLAY environment variable (Linux)
    - Running in Docker container
    - Running on a VPS without desktop
    """
    # macOS always has GUI capability
    if platform.system().lower() == "darwin":
        return False

    # Windows typically has GUI
    if platform.system().lower() == "windows":
        return False

    # Linux: check for DISPLAY
    if not os.environ.get("DISPLAY"):
        return True

    # Check for common headless indicators
    if os.path.exists("/.dockerenv"):
        return True

    # Check if running in SSH session without X forwarding
    if os.environ.get("SSH_CLIENT") and not os.environ.get("DISPLAY"):
        return True

    return False


def is_docker() -> bool:
    """Check if running inside a Docker container"""
    return os.path.exists("/.dockerenv")


def is_ci() -> bool:
    """Check if running in CI environment"""
    ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "TRAVIS"]
    return any(os.environ.get(var) for var in ci_vars)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class BrowserConfig:
    """Browser configuration"""
    headless: bool = True
    slow_mo: int = 0  # Slow down operations by N ms (useful for debugging)
    timeout: int = 30000  # Default timeout in ms
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    ignore_https_errors: bool = False

    # Headless-specific
    use_xvfb: bool = False  # Use Xvfb for headless Linux

    # Local browser specific (CDP)
    cdp_port: int = 9222
    browser_executable: Optional[str] = None


@dataclass
class ScrapingConfig:
    """Scraping behavior configuration"""
    min_delay: float = 2.0  # Minimum delay between requests
    max_delay: float = 5.0  # Maximum delay between requests
    max_pages: int = 100  # Maximum pages to scrape
    max_retries: int = 3  # Retries on failure
    respect_robots_txt: bool = True
    follow_detail_links: bool = True  # Follow detail links
    scroll_for_lazy_load: bool = True  # Auto-scroll for lazy loading


@dataclass
class OutputConfig:
    """Output configuration"""
    default_format: str = "json"  # json, markdown, csv
    output_dir: str = "./scraped_data"
    save_screenshots: bool = True
    compress_output: bool = False


@dataclass
class Config:
    """Main configuration"""
    environment: str = field(default_factory=detect_os)
    is_headless: bool = field(default_factory=is_headless)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    def __post_init__(self):
        # Auto-configure based on environment
        if self.is_headless:
            self.browser.headless = True
            self.output.save_screenshots = False  # No point in screenshots if headless

        # Use Xvfb on headless Linux if available
        if self.is_headless and self.environment == "linux":
            self.browser.use_xvfb = self._check_xvfb()

    def _check_xvfb(self) -> bool:
        """Check if Xvfb is available"""
        import shutil
        return shutil.which("xvfb-run") is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "environment": self.environment,
            "is_headless": self.is_headless,
            "browser": asdict(self.browser),
            "scraping": asdict(self.scraping),
            "output": asdict(self.output)
        }

    def save(self, path: Optional[Path] = None):
        """Save configuration to file"""
        path = path or CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from file"""
        path = path or CONFIG_FILE
        if not path.exists():
            return cls()

        with open(path) as f:
            data = json.load(f)

        config = cls()
        if "browser" in data:
            for k, v in data["browser"].items():
                if hasattr(config.browser, k):
                    setattr(config.browser, k, v)
        if "scraping" in data:
            for k, v in data["scraping"].items():
                if hasattr(config.scraping, k):
                    setattr(config.scraping, k, v)
        if "output" in data:
            for k, v in data["output"].items():
                if hasattr(config.output, k):
                    setattr(config.output, k, v)

        return config


# ============================================================================
# Global Config Getter
# ============================================================================

_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None or reload:
        _config = Config.load()
    return _config


def get_playwright_launch_options() -> Dict[str, Any]:
    """Get Playwright launch options based on config"""
    config = get_config()

    options = {
        "headless": config.browser.headless,
        "slow_mo": config.browser.slow_mo,
    }

    if config.browser.proxy:
        options["proxy"] = {"server": config.browser.proxy}

    if config.browser.browser_executable:
        options["executable_path"] = config.browser.browser_executable

    return options


def get_crawl4ai_config() -> Dict[str, Any]:
    """Get Crawl4AI configuration based on config"""
    config = get_config()

    return {
        "headless": config.browser.headless,
        "viewport_width": config.browser.viewport_width,
        "viewport_height": config.browser.viewport_height,
        "verbose": False,
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    """Print current configuration"""
    config = get_config()

    print("=" * 50)
    print("Intelligent Web Scraper - Configuration")
    print("=" * 50)
    print()
    print(f"Environment: {config.environment}")
    print(f"Headless Mode: {config.is_headless}")
    print()
    print("Browser Settings:")
    print(f"  - Headless: {config.browser.headless}")
    print(f"  - Timeout: {config.browser.timeout}ms")
    print(f"  - Viewport: {config.browser.viewport_width}x{config.browser.viewport_height}")
    print(f"  - Use Xvfb: {config.browser.use_xvfb}")
    print()
    print("Scraping Settings:")
    print(f"  - Delay: {config.scraping.min_delay}-{config.scraping.max_delay}s")
    print(f"  - Max Pages: {config.scraping.max_pages}")
    print(f"  - Follow Detail Links: {config.scraping.follow_detail_links}")
    print(f"  - Scroll for Lazy Load: {config.scraping.scroll_for_lazy_load}")
    print()
    print("Output Settings:")
    print(f"  - Format: {config.output.default_format}")
    print(f"  - Directory: {config.output.output_dir}")
    print()
    print(f"Config file: {CONFIG_FILE}")
    print(f"  {'(exists)' if CONFIG_FILE.exists() else '(not created yet)'}")


if __name__ == "__main__":
    main()
