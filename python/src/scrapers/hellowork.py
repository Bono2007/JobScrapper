import html as htmlmod
import re
from urllib.parse import quote_plus

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.http_client import fetch_page
from src.scrapers.registry import register_scraper

ARIA_PATTERN = re.compile(
    r"Voir offre de (?P<title>.+?) à (?P<location>.+?), chez (?P<company>.+?)"
    r"(?:, super recruteur)?"
    r", pour un (?P<contract>[^,]+)"
    r"(?:, avec un salaire de (?P<salary>.+?€[^,]*))?"
    r"(?:, en (?P<time>[^,]+))?"
    r"(?:, (?P<extra>.+))?"
)


@register_scraper
class HelloWorkScraper(BaseScraper):
    name = "hellowork"
    base_url = "https://www.hellowork.com"

    def build_search_url(self, query: SearchQuery) -> str:
        k = quote_plus(query.keywords)
        loc = quote_plus(query.location)
        return f"{self.base_url}/fr-fr/emploi/recherche.html?k={k}&l={loc}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        raw_html = await fetch_page(url)
        return self._parse_listings(raw_html)

    def _parse_listings(self, raw_html: str) -> list[JobOffer]:
        jobs: list[JobOffer] = []
        seen_urls: set[str] = set()

        for match in re.finditer(
            r'href="(/fr-fr/emplois/\d+\.html)"[^>]*?aria-label="([^"]+)"',
            raw_html,
        ):
            href = match.group(1)
            full_url = f"{self.base_url}{href}"
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            label = htmlmod.unescape(match.group(2))
            aria_match = ARIA_PATTERN.match(label)

            if aria_match:
                jobs.append(
                    JobOffer(
                        title=aria_match.group("title").strip(),
                        company=aria_match.group("company").strip(),
                        location=aria_match.group("location").strip(),
                        url=full_url,
                        source_site=self.name,
                        salary=aria_match.group("salary").strip()
                        if aria_match.group("salary")
                        else None,
                        contract_type=aria_match.group("contract").strip(),
                    )
                )
            else:
                # Fallback: extraire le titre du label brut
                title = label.replace("Voir offre de ", "").split(" à ")[0].strip()
                if title:
                    jobs.append(
                        JobOffer(
                            title=title,
                            company="Non precise",
                            location="Non precise",
                            url=full_url,
                            source_site=self.name,
                        )
                    )

        return jobs
