from urllib.parse import quote_plus

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_json_with_playwright
from src.scrapers.registry import register_scraper

CONTRACT_MAP = {
    "full_time": "CDI",
    "part_time": "Temps partiel",
    "temporary": "CDD",
    "internship": "Stage",
    "apprenticeship": "Alternance",
    "freelance": "Freelance",
    "vie": "VIE",
}


@register_scraper
class WelcomeToTheJungleScraper(BaseScraper):
    name = "welcometothejungle"
    base_url = "https://www.welcometothejungle.com"

    def build_search_url(self, query: SearchQuery) -> str:
        q = quote_plus(query.keywords)
        loc = quote_plus(query.location)
        return f"{self.base_url}/fr/jobs?query={q}&aroundQuery={loc}&aroundRadius={query.radius_km * 1000}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        api_responses = await fetch_json_with_playwright(
            url, api_pattern="indexes/*/queries", timeout=20000
        )

        for response in api_responses:
            # Format multi-index : {"results": [{"hits": [...]}]}
            results = response.get("results", [])
            if results:
                for result in results:
                    hits = result.get("hits", [])
                    if hits:
                        return self._parse_hits(hits)
            # Format single-index : {"hits": [...]}
            hits = response.get("hits", [])
            if hits:
                return self._parse_hits(hits)

        return []

    def _location_matches(self, city: str, query_location: str) -> bool:
        city_l = city.lower().strip()
        loc_l = query_location.lower().strip()
        return loc_l in city_l or city_l in loc_l

    def _parse_hits(self, hits: list[dict]) -> list[JobOffer]:
        jobs: list[JobOffer] = []

        for hit in hits:
            name = hit.get("name", "")
            if not name:
                continue

            org = hit.get("organization", {})
            company = (
                org.get("name", "Non precise")
                if isinstance(org, dict)
                else "Non precise"
            )

            offices = hit.get("offices", [])
            if offices and isinstance(offices, list):
                first = offices[0]
                city = first.get("city", "")
                country = first.get("country", "")
                location = f"{city}, {country}" if city else country
            else:
                location = "Non precise"

            raw_contract = hit.get("contract_type", "")
            contract = CONTRACT_MAP.get(raw_contract, raw_contract)

            salary_min = hit.get("salary_yearly_minimum") or hit.get("salary_minimum")
            salary_max = hit.get("salary_maximum")
            salary_currency = hit.get("salary_currency", "EUR")
            salary_period = hit.get("salary_period", "year")

            salary = None
            if salary_min and salary_max:
                salary = f"{int(salary_min)} - {int(salary_max)} {salary_currency}/{salary_period}"
            elif salary_min:
                salary = f"{int(salary_min)} {salary_currency}/{salary_period}"

            slug = hit.get("slug", "")
            org_ref = org.get("reference", "") if isinstance(org, dict) else ""
            job_url = (
                f"{self.base_url}/fr/companies/{org_ref}/jobs/{slug}"
                if slug and org_ref
                else f"{self.base_url}/fr/jobs"
            )

            jobs.append(
                JobOffer(
                    title=name,
                    company=company,
                    location=location,
                    url=job_url,
                    source_site=self.name,
                    salary=salary,
                    contract_type=contract,
                    description=(hit.get("summary") or hit.get("key_missions") or "")[
                        :500
                    ],
                    published_date=hit.get("published_at"),
                )
            )

        return jobs
