#!/usr/bin/env python3
"""
Reusable Browser Use Cloud session helper.

Provides a context manager for quick browser sessions with
Playwright control, screenshots, and recording.

Usage:
    from browser_session import cloud_browser

    async with cloud_browser(recording=True, proxy="jp") as page:
        await page.goto("https://example.com")
        await page.screenshot(path="shot.png", full_page=True)
    # Session auto-stops, recording URL printed
"""

import asyncio
import os
from contextlib import asynccontextmanager

from browser_use_sdk.v3 import AsyncBrowserUse
from playwright.async_api import async_playwright


@asynccontextmanager
async def cloud_browser(
    api_key=None,
    proxy="us",
    recording=False,
    timeout=15,
    width=1280,
    height=720,
    profile_id=None,
):
    """
    Context manager for a Browser Use Cloud session.

    Args:
        api_key: Browser Use API key. Falls back to BROWSER_USE_API_KEY env var.
        proxy: Country code for proxy (e.g. "us", "jp", "de"). None to disable.
        recording: Enable MP4 video recording.
        timeout: Session timeout in minutes (max 240).
        width: Browser viewport width.
        height: Browser viewport height.
        profile_id: Load a saved browser profile (persistent cookies).

    Yields:
        Playwright Page object for direct browser control.

    Example:
        async with cloud_browser(recording=True, proxy="jp") as page:
            await page.goto("https://example.jp")
            await page.screenshot(path="japan.png")
    """
    if api_key:
        os.environ["BROWSER_USE_API_KEY"] = api_key

    client = AsyncBrowserUse()

    create_kwargs = {
        "enable_recording": recording,
        "timeout": timeout,
        "browser_screen_width": width,
        "browser_screen_height": height,
    }
    if proxy:
        create_kwargs["proxy_country_code"] = proxy
    if profile_id:
        create_kwargs["profile_id"] = profile_id

    browser = await client.browsers.create(**create_kwargs)
    print(f"[cloud-browser] Created: {browser.id}")
    print(f"[cloud-browser] Live: {browser.live_url}")

    async with async_playwright() as p:
        pw_browser = await p.chromium.connect_over_cdp(browser.cdp_url)
        page = pw_browser.contexts[0].pages[0]

        try:
            yield page
        finally:
            await pw_browser.close()

    stopped = await client.browsers.stop(browser.id)
    print(f"[cloud-browser] Stopped. Cost: ${stopped.browser_cost}")
    if stopped.recording_url:
        print(f"[cloud-browser] Recording: {stopped.recording_url}")


# ---------- Standalone demo ----------

async def demo():
    """Quick demo: screenshot example.com"""
    async with cloud_browser(recording=True) as page:
        await page.goto("https://example.com", wait_until="networkidle")
        await page.screenshot(path="demo-screenshot.png", full_page=True)
        print(f"Title: {await page.title()}")
    print("Done! Check demo-screenshot.png")


if __name__ == "__main__":
    asyncio.run(demo())
