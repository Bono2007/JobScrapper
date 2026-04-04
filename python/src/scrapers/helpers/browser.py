from __future__ import annotations

import os
from pathlib import Path

from playwright.async_api import async_playwright


def _get_chromium_executable() -> str | None:
    """
    Returns a path to a usable Chromium-based browser executable.

    Priority:
    1. JOBSCRAPPER_BROWSER env var (override for power users)
    2. Microsoft Edge (always present on Windows 10/11)
    3. Google Chrome
    4. None → Playwright uses its own managed Chromium
    """
    override = os.environ.get("JOBSCRAPPER_BROWSER")
    if override and Path(override).exists():
        return override

    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
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
    timeout: int = 20000,
    wait_until: str = "load",
) -> str:
    from src.scrapers.helpers.browser_pool import acquire_context

    async with acquire_context(viewport={"width": 1280, "height": 800}) as ctx:
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            return await page.content()
        finally:
            await page.close()


async def fetch_json_with_playwright(
    url: str, api_pattern: str, timeout: int = 20000
) -> list[dict]:
    from src.scrapers.helpers.browser_pool import acquire_context

    collected: list[dict] = []

    async with acquire_context() as ctx:
        page = await ctx.new_page()

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
            await page.close()

    return collected
