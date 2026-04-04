import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.http_client import fetch_page
from src.scrapers.registry import register_scraper


@register_scraper
class JobijobaScraper(BaseScraper):
    name = "jobijoba"
    base_url = "https://www.jobijoba.com"

    def build_search_url(self, query: SearchQuery) -> str:
        k = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/fr/recherche?what={k}&where={l}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_page(url)
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []

        # Jobijoba utilise des cartes avec des liens vers /offre/
        for card in soup.find_all(
            ["article", "div", "li"], class_=re.compile(r"job|offer|result|card", re.I)
        ):
            link = card.find("a", href=True)
            if not link:
                continue

            href = link["href"]
            if "/offre/" not in href and "/job/" not in href:
                continue

            title_el = card.find(["h2", "h3", "h4"]) or link
            title = title_el.get_text(strip=True)
            if not title:
                continue

            texts = [
                el.get_text(strip=True)
                for el in card.find_all(["span", "p", "div"])
                if el.get_text(strip=True)
            ]

            company = ""
            location = ""
            salary = ""
            contract_type = ""

            for text in texts:
                if text == title:
                    continue
                if any(
                    ct in text.upper()
                    for ct in ["CDI", "CDD", "ALTERNANCE", "STAGE", "INTERIM"]
                ):
                    if not contract_type:
                        contract_type = text
                elif "€" in text:
                    if not salary:
                        salary = text
                elif not company:
                    company = text
                elif not location:
                    location = text

            full_url = href if href.startswith("http") else f"{self.base_url}{href}"

            jobs.append(
                JobOffer(
                    title=title,
                    company=company or "Non precise",
                    location=location or "Non precise",
                    url=full_url,
                    source_site=self.name,
                    salary=salary or None,
                    contract_type=contract_type or None,
                )
            )

        return jobs
