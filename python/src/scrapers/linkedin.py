import json
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_with_playwright
from src.scrapers.registry import register_scraper


@register_scraper
class LinkedInScraper(BaseScraper):
    name = "linkedin"
    base_url = "https://www.linkedin.com"

    def build_search_url(self, query: SearchQuery) -> str:
        k = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/jobs/search/?keywords={k}&location={l}&distance={query.radius_km}&f_TPR=r2592000&f_JT=F"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_playwright(
            url,
            wait_selector=".jobs-search__results-list,.job-search-card",
            timeout=20000,
        )
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        # LinkedIn public jobs page: liste de <li> avec class job-search-card
        for card in soup.find_all(
            ["li", "div"], class_=re.compile(r"job-search-card|jobs-search__result")
        ):
            link = card.find("a", href=True)
            if not link:
                continue

            href = link["href"]
            # Nettoyer le paramètre de tracking
            clean_url = re.sub(r"\?.*", "", href)
            full_url = (
                clean_url
                if clean_url.startswith("http")
                else f"{self.base_url}{clean_url}"
            )
            if full_url in seen:
                continue
            seen.add(full_url)

            title_el = card.find(
                ["h3", "h2", "span"],
                class_=re.compile(r"base-search-card__title|job-title"),
            )
            title = (
                title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
            )
            if not title:
                continue

            company_el = card.find(
                ["a", "span", "h4"],
                class_=re.compile(r"base-search-card__subtitle|company-name"),
            )
            company = company_el.get_text(strip=True) if company_el else "Non precise"

            loc_el = card.find(
                "span", class_=re.compile(r"job-search-card__location|location")
            )
            location = loc_el.get_text(strip=True) if loc_el else "Non precise"

            date_el = card.find("time")
            published = date_el.get("datetime") if date_el else None

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=full_url,
                    source_site=self.name,
                    published_date=published,
                )
            )

        # Fallback: JSON-LD
        if not jobs:
            jobs = self._parse_json_ld(html)

        return jobs

    def _parse_json_ld(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") != "JobPosting":
                    continue
                org = item.get("hiringOrganization", {})
                company = (
                    org.get("name", "Non precise")
                    if isinstance(org, dict)
                    else "Non precise"
                )
                loc = item.get("jobLocation", {})
                if isinstance(loc, dict):
                    address = loc.get("address", {})
                    location = (
                        address.get("addressLocality", "Non precise")
                        if isinstance(address, dict)
                        else "Non precise"
                    )
                else:
                    location = "Non precise"
                jobs.append(
                    JobOffer(
                        title=item.get("title", ""),
                        company=company,
                        location=location,
                        url=item.get("url", self.base_url),
                        source_site=self.name,
                        published_date=item.get("datePosted"),
                    )
                )
        return jobs
