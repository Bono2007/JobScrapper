from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright


def _get_chromium_executable() -> str | None:
    """
    Returns a path to a usable Chromium-based browser executable.

    Priority:
    1. JOBSCRAPPER_BROWSER env var (override for power users)
    2. Microsoft Edge (always present on Windows 10/11)
    3. Google Chrome (macOS / Windows)
    4. None → Playwright uses its own managed Chromium
    """
    override = os.environ.get("JOBSCRAPPER_BROWSER")
    if override and Path(override).exists():
        return override

    if sys.platform == "win32":
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]

    for p in candidates:
        if Path(p).exists():
            return p

    return None


def _launch_kwargs() -> dict:
    exe = _get_chromium_executable()
    kwargs: dict = {"headless": True}
    if exe:
        kwargs["executable_path"] = exe
    return kwargs


async def fetch_with_playwright(
    url: str,
    wait_selector: str | None = None,
    timeout: int = 30000,
    wait_until: str = "networkidle",
) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(**_launch_kwargs())
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            return await page.content()
        finally:
            await browser.close()


async def fetch_json_with_playwright(
    url: str, api_pattern: str, timeout: int = 30000
) -> list[dict]:
    collected: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(**_launch_kwargs())
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )
        page = await context.new_page()

        async def intercept_response(response) -> None:
            if api_pattern in response.url:
                try:
                    data = await response.json()
                    collected.append(data)
                except Exception:
                    pass

        page.on("response", intercept_response)

        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout)
        finally:
            await browser.close()

    return collected
