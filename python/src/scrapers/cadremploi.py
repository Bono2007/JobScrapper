from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.helpers.browser import fetch_with_playwright
from src.scrapers.registry import register_scraper

_WAIT_SELECTOR = ".job-posting-card"

# Mapping ville → code département pour le paramètre ville= de cadremploi
# Format attendu : "ville-dept" ex: "lille-59"
_CITY_DEPT: dict[str, str] = {
    "paris": "75",
    "marseille": "13",
    "lyon": "69",
    "toulouse": "31",
    "nice": "06",
    "nantes": "44",
    "montpellier": "34",
    "strasbourg": "67",
    "bordeaux": "33",
    "lille": "59",
    "rennes": "35",
    "reims": "51",
    "saint-etienne": "42",
    "toulon": "83",
    "le-havre": "76",
    "grenoble": "38",
    "dijon": "21",
    "angers": "49",
    "nimes": "30",
    "villeurbanne": "69",
    "clermont-ferrand": "63",
    "aix-en-provence": "13",
    "brest": "29",
    "tours": "37",
    "limoges": "87",
    "amiens": "80",
    "perpignan": "66",
    "metz": "57",
    "besancon": "25",
    "boulogne-billancourt": "92",
    "orleans": "45",
    "mulhouse": "68",
    "rouen": "76",
    "caen": "14",
    "nancy": "54",
    "argenteuil": "95",
    "montreuil": "93",
    "roubaix": "59",
    "tourcoing": "59",
    "dunkerque": "59",
    "valenciennes": "59",
    "lens": "62",
    "arras": "62",
    "douai": "59",
    "saint-quentin": "02",
    "compiegne": "60",
    "troyes": "10",
    "pau": "64",
    "bayonne": "64",
    "annecy": "74",
    "chambery": "73",
}


def _build_ville_param(location: str) -> str:
    slug = location.lower().strip().replace(" ", "-")
    dept = _CITY_DEPT.get(slug)
    if dept:
        return f"{slug}-{dept}"
    return slug


@register_scraper
class CadremploiScraper(BaseScraper):
    name = "cadremploi"
    base_url = "https://www.cadremploi.fr"

    def build_search_url(self, query: SearchQuery) -> str:
        keywords = quote_plus(query.keywords)
        ville = _build_ville_param(query.location)
        return f"{self.base_url}/emploi/liste_offres?motscles={keywords}&ville={ville}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_playwright(
            url, wait_selector=_WAIT_SELECTOR, timeout=20000
        )
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen_urls: set[str] = set()

        for card in soup.find_all(class_="job-posting-card"):
            title_el = card.find("a", class_="job-title")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            if not href:
                continue

            full_url = f"{self.base_url}{href}" if not href.startswith("http") else href
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            company_el = card.find(class_="company-name")
            company = company_el.get_text(strip=True) if company_el else "Non précisé"

            chips = [
                p.get_text(strip=True)
                for p in card.select(".v-sheet p.text-pale-grey-20")
            ]
            location = chips[0] if chips else "Non précisé"
            contract_type = chips[1] if len(chips) > 1 else None

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=full_url,
                    source_site=self.name,
                    contract_type=contract_type,
                )
            )

        return jobs
