import os

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.http_client import post_json
from src.scrapers.registry import register_scraper

_API_KEY = os.environ.get("JOOBLE_API_KEY", "")
API_URL = f"https://fr.jooble.org/api/{_API_KEY}" if _API_KEY else ""


@register_scraper
class JoobleScraper(BaseScraper):
    name = "jooble"
    base_url = "https://fr.jooble.org"

    def build_search_url(self, query: SearchQuery) -> str:
        return (
            f"{self.base_url}/SearchResult?ukw={query.keywords}&uloc={query.location}"
        )

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        if not API_URL:
            return []
        payload = {
            "keywords": query.keywords,
            "location": query.location,
            "radius": str(query.radius_km),
            "page": "1",
        }
        data = await post_json(API_URL, payload)
        return self._parse_results(data)

    def _parse_results(self, data: dict) -> list[JobOffer]:
        jobs_data = data.get("jobs", [])
        jobs: list[JobOffer] = []

        for item in jobs_data:
            title = item.get("title", "")
            if not title:
                continue

            # Nettoyer le HTML du titre
            if "<" in title:
                from bs4 import BeautifulSoup

                title = BeautifulSoup(title, "html.parser").get_text(strip=True)

            snippet = item.get("snippet", "")
            if "<" in snippet:
                from bs4 import BeautifulSoup

                snippet = BeautifulSoup(snippet, "html.parser").get_text(strip=True)

            jobs.append(
                JobOffer(
                    title=title,
                    company=item.get("company", "Non precise"),
                    location=item.get("location", "Non precise"),
                    url=item.get("link", ""),
                    source_site=self.name,
                    salary=item.get("salary") or None,
                    contract_type=item.get("type") or None,
                    description=snippet[:500] if snippet else None,
                    published_date=item.get("updated"),
                )
            )

        return jobs
