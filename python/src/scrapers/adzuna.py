"""
Adzuna scraper — scraping direct du site web (sans API key).
"""

from __future__ import annotations

from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_with_playwright
from src.scrapers.registry import register_scraper

_BASE = "https://www.adzuna.fr"
_WAIT_SELECTOR = "article[data-aid]"


@register_scraper
class AdzunaScraper(BaseScraper):
    name = "adzuna"
    base_url = _BASE

    def build_search_url(self, query: SearchQuery) -> str:
        kw = quote_plus(query.keywords)
        loc = quote_plus(query.location)
        return f"{_BASE}/search?q={kw}&w={loc}&ct=permanent"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_playwright(
            url, wait_selector=_WAIT_SELECTOR, timeout=30000, wait_until="load"
        )
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for article in soup.find_all("article", attrs={"data-aid": True}):
            aid = article["data-aid"]

            h2 = article.find("h2")
            link = h2.find("a", attrs={"data-js": "jobLink"}) if h2 else None
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            job_url = link.get("href", f"{_BASE}/land/ad/{aid}")
            if job_url in seen:
                continue
            seen.add(job_url)

            company_el = article.find(class_="ui-company")
            company = company_el.get_text(strip=True) if company_el else "Non précisé"

            loc_el = article.find(class_="ui-location")
            location = loc_el.get_text(strip=True) if loc_el else "Non précisé"

            salary_el = article.find(class_="ui-salary")
            salary = None
            if salary_el:
                raw = salary_el.get_text(" ", strip=True).split("\n")[0].strip()
                if raw and any(c.isdigit() for c in raw):
                    salary = raw

            desc_el = article.find(class_="ui-job-card-body") or article.find("p")
            description = desc_el.get_text(strip=True)[:500] if desc_el else None

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=job_url,
                    source_site=self.name,
                    salary=salary,
                    description=description,
                )
            )

        return jobs
