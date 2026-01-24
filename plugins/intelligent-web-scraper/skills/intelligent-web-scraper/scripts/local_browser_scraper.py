#!/usr/bin/env python3
"""
Local Browser Scraper - Connect to user's running browser via CDP

Connects to Comet, Chrome, or any Chromium-based browser running with
remote debugging enabled. Preserves user's login sessions and cookies.

Usage:
    # First, launch browser with debugging:
    open -a "Comet" --args --remote-debugging-port=9222

    # Then run this script:
    python local_browser_scraper.py --url https://example.com --extract "document.body.innerText"
"""

import asyncio
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import urllib.request

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️ websockets not installed. Run: pip install websockets")


# ============================================================================
# Paths
# ============================================================================

SKILL_DIR = Path.home() / ".claude" / "skills" / "intelligent-web-scraper"
EXPERIENCES_DIR = SKILL_DIR / "experiences"
PATTERNS_FILE = EXPERIENCES_DIR / "site_patterns.json"


# ============================================================================
# Browser Launcher
# ============================================================================

BROWSER_PATHS = {
    "comet": "/Applications/Comet.app/Contents/MacOS/Comet",
    "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "chromium": "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
}

BROWSER_APPS = {
    "comet": "Comet",
    "chrome": "Google Chrome",
    "chromium": "Chromium",
    "edge": "Microsoft Edge",
    "brave": "Brave Browser",
}

# IMPORTANT: Use user's existing profile to preserve login sessions!
# Never use temp directories - they create empty profiles without logins.
BROWSER_USER_DATA_DIRS = {
    "comet": "~/Library/Application Support/Comet",
    "chrome": "~/Library/Application Support/Google/Chrome",
    "chromium": "~/Library/Application Support/Chromium",
    "edge": "~/Library/Application Support/Microsoft Edge",
    "brave": "~/Library/Application Support/BraveSoftware/Brave-Browser",
}


def find_browser(name: str) -> Optional[str]:
    """Find browser executable path"""
    name_lower = name.lower()

    # Check known paths
    if name_lower in BROWSER_PATHS:
        path = BROWSER_PATHS[name_lower]
        if os.path.exists(path):
            return path

    # Try to find by app name
    for key, app_name in BROWSER_APPS.items():
        if name_lower in key or name_lower in app_name.lower():
            path = f"/Applications/{app_name}.app/Contents/MacOS/{app_name}"
            if os.path.exists(path):
                return path

    return None


def is_port_open(port: int) -> bool:
    """Check if a port is open"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0


def launch_browser_with_debugging(
    browser: str = "comet",
    port: int = 9222,
    url: str = "",
    user_data_dir: Optional[str] = None
) -> bool:
    """
    Launch browser with remote debugging enabled

    Args:
        browser: Browser name (comet, chrome, etc.)
        port: Debugging port (default 9222)
        url: Initial URL to open
        user_data_dir: Custom user data directory (None = use existing profile)

    Returns:
        True if browser launched successfully
    """
    # Check if already running on port
    if is_port_open(port):
        print(f"✓ Browser already running on port {port}")
        return True

    browser_path = find_browser(browser)
    if not browser_path:
        print(f"❌ Browser not found: {browser}")
        print(f"   Available browsers: {', '.join(BROWSER_APPS.keys())}")
        return False

    # IMPORTANT: Use user's existing profile to preserve login sessions!
    # Never use temp directories - they create empty profiles without logins.
    if user_data_dir is None:
        browser_lower = browser.lower()
        if browser_lower in BROWSER_USER_DATA_DIRS:
            user_data_dir = os.path.expanduser(BROWSER_USER_DATA_DIRS[browser_lower])
        else:
            # Fallback: try to find existing profile
            user_data_dir = os.path.expanduser(f"~/Library/Application Support/{BROWSER_APPS.get(browser_lower, browser)}")

    # Build command
    cmd = [
        browser_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
    ]

    if url:
        cmd.append(url)

    print(f"🚀 Launching {browser} with debugging on port {port}...")
    print(f"   User data: {user_data_dir}")

    try:
        # Launch browser in background
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Wait for browser to start
        for i in range(10):
            time.sleep(1)
            if is_port_open(port):
                print(f"✓ Browser ready on port {port}")
                return True
            print(f"   Waiting... ({i+1}/10)")

        print("❌ Browser failed to start debugging port")
        return False

    except Exception as e:
        print(f"❌ Failed to launch browser: {e}")
        return False


# ============================================================================
# CDP Connection
# ============================================================================

class CDPConnection:
    """Chrome DevTools Protocol connection"""

    def __init__(self, port: int = 9222):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.ws = None
        self.msg_id = 0

    def get_pages(self) -> List[Dict]:
        """Get list of open pages/tabs"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/json") as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"❌ Cannot connect to browser: {e}")
            print(f"   Make sure browser is running with --remote-debugging-port={self.port}")
            return []

    def get_version(self) -> Optional[Dict]:
        """Get browser version info"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/json/version") as response:
                return json.loads(response.read().decode())
        except:
            return None

    def find_page(self, url_pattern: str) -> Optional[Dict]:
        """Find a page matching URL pattern"""
        pages = self.get_pages()
        for page in pages:
            page_url = page.get('url', '')
            if url_pattern in page_url:
                return page
        return None

    async def connect(self, ws_url: str):
        """Connect to page via WebSocket"""
        self.ws = await websockets.connect(ws_url)

    async def send(self, method: str, params: Dict = None) -> Dict:
        """Send CDP command and get response"""
        self.msg_id += 1
        msg = {
            "id": self.msg_id,
            "method": method,
            "params": params or {}
        }
        await self.ws.send(json.dumps(msg))
        response = await self.ws.recv()
        return json.loads(response)

    async def evaluate(self, expression: str) -> Any:
        """Evaluate JavaScript expression"""
        result = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "result" in result and "result" in result["result"]:
            return result["result"]["result"].get("value")
        return result

    async def close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()


# ============================================================================
# Data Extraction
# ============================================================================

async def extract_with_cdp(
    cdp: CDPConnection,
    ws_url: str,
    extraction_script: str
) -> Any:
    """
    Extract data from page using JavaScript

    Args:
        cdp: CDP connection
        ws_url: WebSocket URL for the page
        extraction_script: JavaScript code to extract data

    Returns:
        Extracted data (usually dict or list)
    """
    await cdp.connect(ws_url)

    try:
        result = await cdp.evaluate(extraction_script)
        return result
    finally:
        await cdp.close()


# ============================================================================
# Common Extraction Scripts
# ============================================================================

EXTRACTION_SCRIPTS = {
    "text": "document.body.innerText",

    "html": "document.body.innerHTML",

    "title": "document.title",

    "links": """
        Array.from(document.querySelectorAll('a')).map(a => ({
            href: a.href,
            text: a.textContent.trim()
        }))
    """,

    "images": """
        Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src,
            alt: img.alt
        }))
    """,

    "tables": """
        Array.from(document.querySelectorAll('table')).map(table => {
            const rows = Array.from(table.querySelectorAll('tr'));
            return rows.map(row => {
                const cells = Array.from(row.querySelectorAll('td, th'));
                return cells.map(cell => cell.textContent.trim());
            });
        })
    """,

    "articles": """
        Array.from(document.querySelectorAll('article')).map(article => ({
            title: article.querySelector('h1, h2, h3')?.textContent?.trim(),
            content: article.textContent.trim().substring(0, 500),
            links: Array.from(article.querySelectorAll('a')).map(a => a.href)
        }))
    """,

    "metadata": """
        ({
            title: document.title,
            description: document.querySelector('meta[name="description"]')?.content,
            url: window.location.href,
            canonical: document.querySelector('link[rel="canonical"]')?.href
        })
    """,
}


# ============================================================================
# Main Functions
# ============================================================================

async def scrape_current_page(
    port: int = 9222,
    url_pattern: str = "",
    extract: str = "text"
) -> Optional[Any]:
    """
    Scrape data from a page in the running browser

    Args:
        port: Debugging port
        url_pattern: Part of URL to find the right tab (empty = first tab)
        extract: Extraction script name or custom JavaScript

    Returns:
        Extracted data
    """
    if not WEBSOCKETS_AVAILABLE:
        print("❌ websockets library required. Run: pip install websockets")
        return None

    cdp = CDPConnection(port)

    # Check browser connection
    version = cdp.get_version()
    if not version:
        print(f"❌ Cannot connect to browser on port {port}")
        print(f"   Launch browser with: --remote-debugging-port={port}")
        return None

    print(f"✓ Connected to {version.get('Browser', 'browser')}")

    # Find target page
    pages = cdp.get_pages()
    if not pages:
        print("❌ No pages found")
        return None

    target = None
    if url_pattern:
        target = cdp.find_page(url_pattern)
        if not target:
            print(f"❌ No page matching '{url_pattern}'")
            print("   Available pages:")
            for p in pages[:5]:
                print(f"   - {p.get('url', 'unknown')}")
            return None
    else:
        # Use first page
        target = pages[0]

    print(f"📄 Target: {target.get('url', 'unknown')[:80]}")

    ws_url = target.get('webSocketDebuggerUrl')
    if not ws_url:
        print("❌ Page doesn't have WebSocket URL")
        return None

    # Get extraction script
    if extract in EXTRACTION_SCRIPTS:
        script = EXTRACTION_SCRIPTS[extract]
    else:
        script = extract

    print(f"🔍 Extracting data...")

    data = await extract_with_cdp(cdp, ws_url, script)

    return data


async def scrape_with_navigation(
    port: int = 9222,
    url: str = "",
    extract: str = "text",
    wait: float = 2.0
) -> Optional[Any]:
    """
    Navigate to URL and scrape data

    Args:
        port: Debugging port
        url: URL to navigate to
        extract: Extraction script
        wait: Seconds to wait after navigation

    Returns:
        Extracted data
    """
    if not WEBSOCKETS_AVAILABLE:
        print("❌ websockets library required")
        return None

    cdp = CDPConnection(port)

    pages = cdp.get_pages()
    if not pages:
        print("❌ No pages found. Open a tab first.")
        return None

    target = pages[0]
    ws_url = target.get('webSocketDebuggerUrl')

    await cdp.connect(ws_url)

    try:
        # Navigate to URL
        print(f"🔗 Navigating to {url[:60]}...")
        await cdp.send("Page.navigate", {"url": url})

        # Wait for load
        print(f"⏳ Waiting {wait}s for page load...")
        await asyncio.sleep(wait)

        # Extract
        if extract in EXTRACTION_SCRIPTS:
            script = EXTRACTION_SCRIPTS[extract]
        else:
            script = extract

        print(f"🔍 Extracting...")
        result = await cdp.evaluate(script)

        return result

    finally:
        await cdp.close()


# ============================================================================
# CLI Entry Point
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description='Scrape data from local browser via CDP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape current page text
  python local_browser_scraper.py --extract text

  # Scrape specific tab
  python local_browser_scraper.py --url-pattern "douban.com" --extract articles

  # Navigate and scrape
  python local_browser_scraper.py --url https://example.com --extract metadata

  # Custom JavaScript extraction
  python local_browser_scraper.py --extract "document.querySelectorAll('h1').length"

  # Launch browser with debugging
  python local_browser_scraper.py --launch comet --url https://example.com

Built-in extractors: text, html, title, links, images, tables, articles, metadata
        """
    )

    parser.add_argument('--port', '-p', type=int, default=9222,
                        help='Browser debugging port (default: 9222)')
    parser.add_argument('--url', '-u', help='URL to navigate to')
    parser.add_argument('--url-pattern', help='Find tab matching this URL pattern')
    parser.add_argument('--extract', '-e', default='text',
                        help='Extraction: text, html, links, images, tables, articles, metadata, or custom JS')
    parser.add_argument('--wait', '-w', type=float, default=2.0,
                        help='Wait time after navigation (default: 2.0s)')
    parser.add_argument('--output', '-o', help='Output file (JSON)')
    parser.add_argument('--launch', '-l', help='Launch browser (comet, chrome, etc.)')
    parser.add_argument('--user-data-dir', help='Custom user data directory')
    parser.add_argument('--list-pages', action='store_true',
                        help='List all open pages and exit')

    args = parser.parse_args()

    # Launch browser if requested
    if args.launch:
        success = launch_browser_with_debugging(
            browser=args.launch,
            port=args.port,
            url=args.url or "",
            user_data_dir=args.user_data_dir
        )
        if not success:
            return
        # If just launching without extraction, we're done
        if not args.extract or args.extract == 'text':
            print("\n✓ Browser ready. Run again with --extract to scrape data.")
            return

    # List pages if requested
    if args.list_pages:
        cdp = CDPConnection(args.port)
        pages = cdp.get_pages()
        if pages:
            print(f"\n📋 Open pages ({len(pages)}):\n")
            for i, page in enumerate(pages):
                print(f"{i+1}. {page.get('title', 'Untitled')[:50]}")
                print(f"   {page.get('url', 'unknown')[:70]}")
                print()
        else:
            print("No pages found. Is browser running with --remote-debugging-port?")
        return

    # Scrape data
    if args.url:
        data = await scrape_with_navigation(
            port=args.port,
            url=args.url,
            extract=args.extract,
            wait=args.wait
        )
    else:
        data = await scrape_current_page(
            port=args.port,
            url_pattern=args.url_pattern or "",
            extract=args.extract
        )

    if data is not None:
        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ Saved to {args.output}")
        else:
            print("\n📦 Result:")
            if isinstance(data, (dict, list)):
                print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
            else:
                print(str(data)[:2000])

            if isinstance(data, str) and len(data) > 2000:
                print(f"\n... (truncated, total {len(data)} chars)")


if __name__ == '__main__':
    asyncio.run(main())
