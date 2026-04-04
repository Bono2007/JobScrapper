"""
Pool de browsers Playwright partagé entre tous les scrapers.

Utilise une file de N browsers pré-lancés au démarrage de l'app.
Chaque scraper prend un browser libre, crée son contexte isolé, puis
remet le browser dans la file. Si un browser crashe, les autres
continuent — les crashes sont isolés.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from src.scrapers.helpers.browser import _launch_kwargs

_playwright: Playwright | None = None
_browser_queue: asyncio.Queue | None = None

# Nombre de browsers pré-lancés. 3 = bon équilibre vitesse / mémoire.
# 8 scrapers Playwright → les 3 premiers démarrent immédiatement (browser déjà chaud),
# les suivants attendent qu'un slot se libère.
POOL_SIZE = 3

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


async def init_pool() -> None:
    global _playwright, _browser_queue
    _playwright = await async_playwright().start()
    _browser_queue = asyncio.Queue()
    for _ in range(POOL_SIZE):
        browser = await _playwright.chromium.launch(**_launch_kwargs())
        await _browser_queue.put(browser)


async def close_pool() -> None:
    global _playwright, _browser_queue
    if _browser_queue:
        while not _browser_queue.empty():
            browser: Browser = _browser_queue.get_nowait()
            try:
                await browser.close()
            except Exception:
                pass
        _browser_queue = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def _get_healthy_browser() -> Browser:
    """Retourne un browser vivant du pool, en relançant si nécessaire."""
    browser: Browser = await _browser_queue.get()
    if not browser.is_connected():
        try:
            browser = await _playwright.chromium.launch(**_launch_kwargs())
        except Exception:
            pass
    return browser


@asynccontextmanager
async def acquire_context(**context_kwargs) -> AsyncGenerator[BrowserContext, None]:
    """Acquiert un browser du pool, crée un contexte isolé, puis remet le browser."""
    if _browser_queue is None:
        raise RuntimeError("Browser pool not initialized — call init_pool() first")

    context_kwargs.setdefault("user_agent", _UA)
    context_kwargs.setdefault("locale", "fr-FR")

    browser = await _get_healthy_browser()
    ctx: BrowserContext | None = None
    try:
        ctx = await browser.new_context(**context_kwargs)
        yield ctx
    finally:
        if ctx:
            try:
                await ctx.close()
            except Exception:
                pass
        # Remet le browser dans la file (même s'il a crashé — _get_healthy_browser
        # le détectera et le remplacera au prochain appel)
        await _browser_queue.put(browser)
