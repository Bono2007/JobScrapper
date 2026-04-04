"""
France Travail scraper — scraping direct du site candidat (sans API key).
Utilise l'API publique de suggestion géographique pour résoudre le code commune.
"""

from __future__ import annotations

from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_with_playwright
from src.scrapers.registry import register_scraper

_BASE = "https://candidat.francetravail.fr"
_SUGGEST_URL = (
    "https://api.francetravail.fr/exp-rechercheoffre/geo/v1/territorial/lieu/requete"
)
_WAIT_SELECTOR = "li.result"


@register_scraper
class FranceTravailScraper(BaseScraper):
    name = "francetravail"
    base_url = _BASE

    def build_search_url(self, query: SearchQuery) -> str:
        return (
            f"{_BASE}/offres/recherche"
            f"?motsCles={quote_plus(query.keywords)}"
            f"&offresPartenaires=true&rayon={query.radius_km}&tri=0"
        )

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        code_commune = await self._get_commune_code(query.location)
        kw = quote_plus(query.keywords)
        if code_commune:
            url = (
                f"{_BASE}/offres/recherche"
                f"?lieux={code_commune}&motsCles={kw}"
                f"&offresPartenaires=true&rayon={query.radius_km}"
                f"&typeContrat=CDI&tri=0"
            )
        else:
            url = (
                f"{_BASE}/offres/recherche"
                f"?motsCles={kw}&offresPartenaires=true"
                f"&typeContrat=CDI&tri=0"
            )

        html = await fetch_with_playwright(
            url, wait_selector=_WAIT_SELECTOR, timeout=20000, wait_until="load"
        )
        return self._parse_listings(html)

    async def _get_commune_code(self, city: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    _SUGGEST_URL,
                    params={
                        "q": city,
                        "nbmaxpartypelieu": 5,
                        "typeLieu": "COMMUNE",
                    },
                )
                data = resp.json()
                results = data.get("resultats", [])
                communes = [r for r in results if r.get("typeLieu") == "COMMUNE"]
                if communes:
                    return communes[0]["codeCommune"]
        except Exception:
            pass
        return None

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for li in soup.find_all("li", class_="result"):
            aid = li.get("data-id-offre", "")
            link = li.find("a", class_="media")
            if not link:
                continue

            href = link.get("href", "")
            job_url = f"{_BASE}{href}" if href.startswith("/") else href
            if job_url in seen:
                continue
            seen.add(job_url)

            title_el = li.find("span", class_="media-heading-title")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            loc_el = li.find("p", class_="subtext")
            location = loc_el.get_text(strip=True) if loc_el else "Non précisé"

            desc_el = li.find("p", class_="description")
            description = desc_el.get_text(strip=True)[:500] if desc_el else None

            contrat_el = li.find("p", class_="contrat")
            contract_type = None
            if contrat_el:
                raw = contrat_el.get_text(" ", strip=True)
                contract_type = raw.split("\n")[0].strip() or None

            jobs.append(
                JobOffer(
                    title=title,
                    company="Non précisé",
                    location=location,
                    url=job_url,
                    source_site=self.name,
                    contract_type=contract_type,
                    description=description,
                )
            )

        return jobs
