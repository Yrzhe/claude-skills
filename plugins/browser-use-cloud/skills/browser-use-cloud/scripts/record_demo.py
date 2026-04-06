#!/usr/bin/env python3
"""
Record a browser session as MP4 video.

Takes a URL, performs navigation and interactions, then downloads
the recording as an MP4 file.

Usage:
    export BROWSER_USE_API_KEY="bu_xxx"
    python3 record_demo.py https://example.com output.mp4

    # With proxy country
    python3 record_demo.py https://amazon.co.jp output.mp4 --proxy jp

    # Full page screenshot too
    python3 record_demo.py https://example.com output.mp4 --screenshot shot.png
"""

import argparse
import asyncio
import os
import urllib.request

from browser_use_sdk.v3 import AsyncBrowserUse
from playwright.async_api import async_playwright


async def record(url, output, proxy="us", screenshot=None, scroll=True, wait=3):
    client = AsyncBrowserUse()

    print(f"[record] Creating browser (proxy={proxy})...")
    browser = await client.browsers.create(
        proxy_country_code=proxy,
        enable_recording=True,
        timeout=10,
    )
    print(f"[record] Live: {browser.live_url}")

    async with async_playwright() as p:
        pw = await p.chromium.connect_over_cdp(browser.cdp_url)
        page = pw.contexts[0].pages[0]

        print(f"[record] Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        print(f"[record] Title: {await page.title()}")

        if screenshot:
            await page.screenshot(path=screenshot, full_page=True)
            print(f"[record] Screenshot: {screenshot}")

        if scroll:
            # Smooth scroll for recording
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(r => setTimeout(r, ms));
                    const h = document.body.scrollHeight;
                    const step = Math.floor(h / 5);
                    for (let i = 0; i < 5; i++) {
                        window.scrollBy(0, step);
                        await delay(800);
                    }
                    window.scrollTo(0, 0);
                    await delay(500);
                }
            """)

        # Hold for a moment so recording captures final state
        await page.wait_for_timeout(wait * 1000)
        await pw.close()

    print("[record] Stopping browser...")
    stopped = await client.browsers.stop(browser.id)
    print(f"[record] Cost: ${stopped.browser_cost}")

    if stopped.recording_url:
        print(f"[record] Downloading recording...")
        urllib.request.urlretrieve(stopped.recording_url, output)
        size = os.path.getsize(output)
        print(f"[record] Saved: {output} ({size:,} bytes)")
    else:
        print("[record] No recording URL returned")


def main():
    parser = argparse.ArgumentParser(description="Record a browser session as MP4")
    parser.add_argument("url", help="URL to visit")
    parser.add_argument("output", help="Output MP4 file path")
    parser.add_argument("--proxy", default="us", help="Proxy country code (default: us)")
    parser.add_argument("--screenshot", help="Also save a full-page screenshot")
    parser.add_argument("--no-scroll", action="store_true", help="Skip auto-scrolling")
    parser.add_argument("--wait", type=int, default=3, help="Seconds to wait before stopping")
    args = parser.parse_args()

    asyncio.run(record(
        args.url, args.output,
        proxy=args.proxy,
        screenshot=args.screenshot,
        scroll=not args.no_scroll,
        wait=args.wait,
    ))


if __name__ == "__main__":
    main()
