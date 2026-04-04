import json
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.http_client import fetch_page
from src.scrapers.registry import register_scraper


@register_scraper
class MonsterScraper(BaseScraper):
    name = "monster"
    base_url = "https://www.monster.com"

    def build_search_url(self, query: SearchQuery) -> str:
        q = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/jobs/search?q={q}&where={l}&lang=fr"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_page(url)
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        # Essayer d'extraire les donnees JSON-LD d'abord
        jobs = self._try_json_ld(html)
        if jobs:
            return jobs
        # Fallback HTML
        return self._parse_html(html)

    def _try_json_ld(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if data.get("@type") == "JobPosting":
                    items = [data]
                elif "itemListElement" in data:
                    items = [el.get("item", el) for el in data["itemListElement"]]

            for item in items:
                if item.get("@type") != "JobPosting":
                    continue

                org = item.get("hiringOrganization", {})
                company = (
                    org.get("name", "Non precise")
                    if isinstance(org, dict)
                    else str(org)
                )

                loc = item.get("jobLocation", {})
                if isinstance(loc, dict):
                    address = loc.get("address", {})
                    location = (
                        address.get("addressLocality", "Non precise")
                        if isinstance(address, dict)
                        else str(address)
                    )
                elif isinstance(loc, list) and loc:
                    address = loc[0].get("address", {})
                    location = (
                        address.get("addressLocality", "Non precise")
                        if isinstance(address, dict)
                        else ""
                    )
                else:
                    location = "Non precise"

                salary_data = item.get("baseSalary", {})
                salary = None
                if isinstance(salary_data, dict):
                    value = salary_data.get("value", {})
                    if isinstance(value, dict):
                        min_val = value.get("minValue", "")
                        max_val = value.get("maxValue", "")
                        if min_val and max_val:
                            salary = f"{min_val} - {max_val} {salary_data.get('currency', 'EUR')}"

                jobs.append(
                    JobOffer(
                        title=item.get("title", ""),
                        company=company,
                        location=location,
                        url=item.get("url", ""),
                        source_site=self.name,
                        salary=salary,
                        contract_type=item.get("employmentType"),
                        description=(item.get("description", "") or "")[:500],
                        published_date=item.get("datePosted"),
                    )
                )

        return jobs

    def _parse_html(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []

        for card in soup.find_all(
            ["div", "article", "li"],
            class_=re.compile(r"job-cardstyle|job-search-card|results", re.I),
        ):
            link = card.find("a", href=True)
            if not link:
                continue

            title_el = card.find(["h2", "h3"]) or link
            title = title_el.get_text(strip=True)
            if not title:
                continue

            href = link["href"]
            full_url = href if href.startswith("http") else f"{self.base_url}{href}"

            company_el = card.find("span", class_=re.compile(r"company", re.I))
            company = company_el.get_text(strip=True) if company_el else "Non precise"

            loc_el = card.find("span", class_=re.compile(r"location", re.I))
            location = loc_el.get_text(strip=True) if loc_el else "Non precise"

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=full_url,
                    source_site=self.name,
                )
            )

        return jobs
