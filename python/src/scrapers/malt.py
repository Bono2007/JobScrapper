from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_with_playwright
from src.scrapers.registry import register_scraper


@register_scraper
class MaltScraper(BaseScraper):
    name = "malt"
    base_url = "https://www.malt.fr"

    def build_search_url(self, query: SearchQuery) -> str:
        k = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/search?q={k}&location={l}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_playwright(
            url,
            wait_selector="[class*='mission'],[class*='card']",
            timeout=30000,
            wait_until="load",
        )
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/mission/" not in href and "/projet/" not in href:
                continue
            full_url = href if href.startswith("http") else f"{self.base_url}{href}"
            if full_url in seen:
                continue
            seen.add(full_url)

            title_el = link.find(["h2", "h3", "h4"]) or link
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            card = link.find_parent(["article", "li", "div"])
            company, location, salary = "Mission freelance", "Non precise", None
            if card:
                for el in card.find_all(["span", "p"]):
                    text = el.get_text(strip=True)
                    if not text or text == title:
                        continue
                    if "€" in text and not salary:
                        salary = text
                    elif location == "Non precise":
                        location = text

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=full_url,
                    source_site=self.name,
                    salary=salary,
                    contract_type="Freelance",
                )
            )

        return jobs
