from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.registry import register_scraper


@register_scraper
class CadresOnlineScraper(BaseScraper):
    name = "cadresonline"
    base_url = "https://www.cadresonline.com"

    def build_search_url(self, query: SearchQuery) -> str:
        k = quote_plus(query.keywords)
        l = quote_plus(query.location)
        return f"{self.base_url}/emploi/offres-emploi/?k={k}&l={l}"

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        html = await fetch_with_curl(url)
        return self._parse_listings(html)

    def _parse_listings(self, html: str) -> list[JobOffer]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/emploi/offre/" not in href and "/offre-emploi/" not in href:
                continue
            full_url = href if href.startswith("http") else f"{self.base_url}{href}"
            if full_url in seen:
                continue
            seen.add(full_url)

            title_el = link.find(["h2", "h3", "h4"]) or link
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            card = link.find_parent(["article", "li", "div"])
            company, location, contract_type, salary = (
                "Non precise",
                "Non precise",
                None,
                None,
            )
            if card:
                for el in card.find_all(["span", "p", "strong"]):
                    text = el.get_text(strip=True)
                    if not text or text == title:
                        continue
                    upper = text.upper()
                    if any(k in upper for k in ["CDI", "CDD", "FREELANCE", "STAGE"]):
                        if not contract_type:
                            contract_type = text
                    elif "€" in text and not salary:
                        salary = text
                    elif company == "Non precise":
                        company = text
                    elif location == "Non precise":
                        location = text

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location,
                    url=full_url,
                    source_site=self.name,
                    salary=salary,
                    contract_type=contract_type,
                )
            )

        return jobs
