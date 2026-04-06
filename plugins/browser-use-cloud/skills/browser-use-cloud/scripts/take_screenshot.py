#!/usr/bin/env python3
"""
Take a screenshot of any URL using Browser Use Cloud.

Supports anti-detection, proxy routing, and full-page capture.

Usage:
    export BROWSER_USE_API_KEY="bu_xxx"
    python3 take_screenshot.py https://example.com screenshot.png
    python3 take_screenshot.py https://amazon.co.jp japan.png --proxy jp
    python3 take_screenshot.py https://example.com full.png --full-page
"""

import argparse
import asyncio
import os

from browser_use_sdk.v3 import AsyncBrowserUse
from playwright.async_api import async_playwright


async def screenshot(url, output, proxy="us", full_page=False):
    client = AsyncBrowserUse()

    browser = await client.browsers.create(
        proxy_country_code=proxy,
        timeout=5,
    )

    async with async_playwright() as p:
        pw = await p.chromium.connect_over_cdp(browser.cdp_url)
        page = pw.contexts[0].pages[0]
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.screenshot(path=output, full_page=full_page)
        title = await page.title()
        print(f"Title: {title}")
        await pw.close()

    stopped = await client.browsers.stop(browser.id)
    size = os.path.getsize(output)
    print(f"Screenshot: {output} ({size:,} bytes)")
    print(f"Cost: ${stopped.browser_cost}")


def main():
    parser = argparse.ArgumentParser(description="Screenshot a URL via cloud browser")
    parser.add_argument("url", help="URL to screenshot")
    parser.add_argument("output", help="Output image path (.png)")
    parser.add_argument("--proxy", default="us", help="Proxy country (default: us)")
    parser.add_argument("--full-page", action="store_true", help="Capture full page")
    args = parser.parse_args()
    asyncio.run(screenshot(args.url, args.output, args.proxy, args.full_page))


if __name__ == "__main__":
    main()
