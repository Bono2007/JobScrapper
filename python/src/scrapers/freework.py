from urllib.parse import urlencode

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.http_client import fetch_json
from src.scrapers.registry import register_scraper

_API_URL = "https://www.free-work.com/api/job_postings"
_BASE_URL = "https://www.free-work.com"

# Mapping contract_type → free-work API value
_CONTRACT_MAP = {
    "cdi": "permanent",
    "permanent": "permanent",
    "freelance": "contractor",
    "contractor": "contractor",
    "cdd": "fixed_term",
}


@register_scraper
class FreeWorkScraper(BaseScraper):
    name = "free-work"
    base_url = _BASE_URL

    def build_search_url(self, query: SearchQuery) -> str:
        params = self._build_params(query)
        return f"{_API_URL}?{urlencode(params)}"

    def _build_params(self, query: SearchQuery) -> dict:
        params: dict = {
            "page": 1,
            "itemsPerPage": query.max_results_per_site,
            "locationKeys": "fr~~~",
            "searchKeywords": query.keywords,
        }
        if query.radius_km:
            params["radius"] = query.radius_km
        if query.contract_type:
            fw_contract = _CONTRACT_MAP.get(query.contract_type.lower())
            if fw_contract:
                params["contracts"] = fw_contract
        return params

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        params = self._build_params(query)
        data = await fetch_json(_API_URL, params=params)
        # API returns a list with Accept: application/json, or hydra dict with ld+json
        if isinstance(data, list):
            members = data
        else:
            members = data.get("hydra:member", [])
        return self._parse_results(members)

    def _parse_results(self, members: list[dict]) -> list[JobOffer]:
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for item in members:
            slug = item.get("slug", "")
            url = f"{_BASE_URL}/fr/tech-it/jobs/{slug}" if slug else _BASE_URL
            if url in seen:
                continue
            seen.add(url)

            title = item.get("title", "").strip()
            if not title:
                continue

            company_obj = item.get("company") or {}
            company = company_obj.get("name", "Non précisé") if isinstance(company_obj, dict) else "Non précisé"

            loc_obj = item.get("location") or {}
            location = loc_obj.get("label", loc_obj.get("shortLabel", "Non précisé")) if isinstance(loc_obj, dict) else "Non précisé"

            # Salary: prefer annual, fallback to daily
            salary: str | None = None
            min_a = item.get("minAnnualSalary")
            max_a = item.get("maxAnnualSalary")
            min_d = item.get("minDailySalary")
            max_d = item.get("maxDailySalary")
            if min_a or max_a:
                salary = f"{min_a or ''}-{max_a or ''} EUR/an".strip("- ")
            elif min_d or max_d:
                salary = f"{min_d or ''}-{max_d or ''} EUR/j".strip("- ")

            # Contract types
            contracts_raw = item.get("contracts", [])
            contract_labels = [
                c.get("label", c) if isinstance(c, dict) else str(c)
                for c in contracts_raw
            ]
            contract_type = ", ".join(contract_labels) if contract_labels else None

            published = item.get("publishedAt") or item.get("createdAt")

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    source_site=self.name,
                    salary=salary,
                    contract_type=contract_type,
                    published_date=published,
                )
            )

        return jobs
