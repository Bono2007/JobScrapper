from playwright.async_api import async_playwright


async def fetch_with_playwright(
    url: str,
    wait_selector: str | None = None,
    timeout: int = 30000,
    wait_until: str = "networkidle",
) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
        browser = await p.chromium.launch(headless=True)
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
