from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import (
    fetch_json_with_playwright,
    fetch_with_playwright,
)
from src.scrapers.registry import register_scraper

# APEC API endpoint intercepted from browser network traffic
_API_PATTERN = "rechercheOffre"
_WAIT_SELECTOR = ".container-result"

# Mapping of APEC numeric typeContrat IDs to readable labels
_CONTRACT_TYPE_LABELS: dict[int, str] = {
    101888: "CDI",
    101889: "CDD",
    597137: "Alternance",
    101892: "Stage",
    101891: "Intérim",
    101890: "Indépendant",
}


@register_scraper
class ApecScraper(BaseScraper):
    name = "apec"
    base_url = "https://www.apec.fr"

    def build_search_url(self, query: SearchQuery) -> str:
        keywords = quote_plus(query.keywords)
        location_encoded = quote_plus(query.location)
        return (
            f"{self.base_url}/candidat/recherche-emploi.html/emploi"
            f"?motsCles={keywords}&lieuTravail={location_encoded}"
            f"&typesContrats=101888&page=1"
        )

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)

        # Primary: intercept the internal JSON API call made by the SPA
        api_calls = await fetch_json_with_playwright(
            url,
            api_pattern=_API_PATTERN,
            timeout=30000,
        )

        for response in api_calls:
            resultats = response.get("resultats", [])
            if resultats:
                jobs = self._parse_api_results(resultats)
                return self._filter_by_location(jobs, query.location)

        # Fallback: parse rendered HTML
        html = await fetch_with_playwright(
            url, wait_selector=_WAIT_SELECTOR, timeout=30000
        )
        jobs = self._parse_html(html)
        return self._filter_by_location(jobs, query.location)

    def _filter_by_location(
        self, jobs: list[JobOffer], query_location: str
    ) -> list[JobOffer]:
        if not query_location:
            return jobs
        loc_lower = query_location.lower().strip()
        return [j for j in jobs if loc_lower in j.location.lower()]

    def _parse_api_results(self, results: list[dict]) -> list[JobOffer]:
        jobs: list[JobOffer] = []
        for item in results:
            # Real field names confirmed from live API inspection
            numero_offre = item.get("numeroOffre", "")
            title = item.get("intitule", "")
            if not title:
                continue

            # Company: nomCommercial is absent for confidential offers
            company = item.get("nomCommercial") or "Confidentiel"

            # Location: lieuTexte is a plain string like "Lille - 59"
            location = item.get("lieuTexte") or "Non précisé"

            salary = item.get("salaireTexte") or None
            if salary and salary.strip().lower() == "a négocier":
                salary = None

            contract_type_id = item.get("typeContrat")
            contract_type = (
                _CONTRACT_TYPE_LABELS.get(contract_type_id)
                if contract_type_id
                else None
            )

            offer_url = (
                f"{self.base_url}/candidat/recherche-emploi.html/emploi/detail-offre/{numero_offre}"
                if numero_offre
                else self.base_url
            )

            published_date = item.get("datePublication") or item.get("dateValidation")

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=offer_url,
                    source_site=self.name,
                    salary=salary,
                    contract_type=contract_type,
                    published_date=published_date,
                )
            )
        return jobs

    def _parse_html(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for card in soup.find_all(class_="container-result"):
            link = card.find("a", href=True)
            if not link:
                continue
            href = link["href"]
            if "detail-offre" not in href:
                continue

            full_url = href if href.startswith("http") else f"{self.base_url}{href}"
            # Strip query params from URL for deduplication
            base_offer_url = full_url.split("?")[0]
            if base_offer_url in seen:
                continue
            seen.add(base_offer_url)

            title_el = card.find("h2", class_="card-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            company_el = card.find(class_="card-offer__company")
            company = company_el.get_text(strip=True) if company_el else "Non précisé"

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location="Non précisé",
                    url=base_offer_url,
                    source_site=self.name,
                )
            )

        return jobs
