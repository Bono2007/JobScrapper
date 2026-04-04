from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_with_playwright
from src.scrapers.registry import register_scraper


@register_scraper
class WizbiScraper(BaseScraper):
    name = "wizbii"
    base_url = "https://www.wizbii.com"

    def build_search_url(self, query: SearchQuery) -> str:
        k = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/emploi/cdi?q={k}&location={l}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_playwright(
            url,
            wait_selector="[class*='job'],[class*='offer'],[class*='card']",
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
            if "/jobs/" not in href and "/job/" not in href:
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
            company, location, contract_type, salary = (
                "Non precise",
                "Non precise",
                None,
                None,
            )
            if card:
                for el in card.find_all(["span", "p", "div"]):
                    text = el.get_text(strip=True)
                    if not text or text == title:
                        continue
                    upper = text.upper()
                    if any(k in upper for k in ["CDI", "CDD", "STAGE", "ALTERNANCE"]):
                        if not contract_type:
                            contract_type = text
                    elif "€" in text and not salary:
                        salary = text
                    elif company == "Non precise":
                        company = text
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
                    contract_type=contract_type,
                )
            )

        return jobs
