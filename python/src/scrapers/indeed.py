import json
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.http_client import fetch_with_curl
from src.scrapers.registry import register_scraper


@register_scraper
class IndeedScraper(BaseScraper):
    name = "indeed"
    base_url = "https://fr.indeed.com"

    def build_search_url(self, query: SearchQuery) -> str:
        q = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/jobs?q={q}&l={l}&radius={query.radius_km}&jt=fulltime"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_curl(url)
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        jobs = self._try_parse_json_data(html)
        if not jobs:
            jobs = self._parse_html(html)
        # Deduplication par URL
        seen: set[str] = set()
        unique: list[JobOffer] = []
        for job in jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique.append(job)
        return unique

    def _try_parse_json_data(self, html: str) -> list[JobOffer]:
        pattern = r"window\._initialData\s*=\s*(\{.*?\});"
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        jobs: list[JobOffer] = []
        results = self._extract_results(data)

        for result in results:
            job_data = result.get("job", result)
            title = job_data.get("title", "")
            company = job_data.get(
                "sourceEmployerName", job_data.get("company", "Non precise")
            )
            location_data = job_data.get("location", {})
            if isinstance(location_data, dict):
                formatted = location_data.get("formatted", {})
                location = formatted.get("short", formatted.get("long", ""))
            else:
                location = str(location_data)

            job_types = job_data.get("jobTypes", [])
            contract = (
                ", ".join(jt.get("label", "") for jt in job_types)
                if job_types
                else None
            )

            job_key = result.get("jobkey", job_data.get("key", ""))
            url = f"{self.base_url}/viewjob?jk={job_key}" if job_key else ""

            if title and url:
                jobs.append(
                    JobOffer(
                        title=title,
                        company=company or "Non precise",
                        location=location or "Non precise",
                        url=url,
                        source_site=self.name,
                        contract_type=contract,
                    )
                )

        # Deduplication par URL
        seen: set[str] = set()
        unique: list[JobOffer] = []
        for job in jobs:
            if job.url not in seen:
                seen.add(job.url)
                unique.append(job)
        return unique

    def _extract_results(self, data: dict) -> list[dict]:
        # Navigue dans la structure imbriquee d'Indeed
        try:
            host = data.get("hostQueryExecutionResult", {})
            job_data = host.get("data", {}).get("jobData", {})
            return job_data.get("results", [])
        except (AttributeError, TypeError):
            pass

        # Fallback: chercher recursivement
        if "results" in data:
            return data["results"]

        for value in data.values():
            if isinstance(value, dict):
                found = self._extract_results(value)
                if found:
                    return found

        return []

    def _parse_html(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []

        for card in soup.find_all(
            "div", class_=re.compile(r"job_seen_beacon|cardOutline|result")
        ):
            title_el = card.find("h2") or card.find(
                "a", class_=re.compile(r"jcs-JobTitle")
            )
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.find("a", href=True) if title_el.name != "a" else title_el
            href = link["href"] if link and link.get("href") else ""
            url = (
                f"{self.base_url}{href}"
                if href and not href.startswith("http")
                else href
            )

            company_el = card.find(
                "span", class_=re.compile(r"company|css-")
            ) or card.find(attrs={"data-testid": "company-name"})
            company = company_el.get_text(strip=True) if company_el else "Non precise"

            loc_el = card.find(attrs={"data-testid": "text-location"}) or card.find(
                "div", class_=re.compile(r"company_location")
            )
            location = loc_el.get_text(strip=True) if loc_el else "Non precise"

            if title and url:
                jobs.append(
                    JobOffer(
                        title=title,
                        company=company,
                        location=location,
                        url=url,
                        source_site=self.name,
                    )
                )

        return jobs
