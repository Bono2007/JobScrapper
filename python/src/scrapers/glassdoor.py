"""
Glassdoor scraper — Next.js RSC interception sur glassdoor.com.
Charge la page de résultats via Playwright, intercepte le payload RSC
(self.__next_f.push) qui contient les offres embarquées côté serveur.
"""

from __future__ import annotations

import json
import unicodedata

from playwright.async_api import async_playwright

from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.base import BaseScraper
from src.scrapers.registry import register_scraper

_BASE = "https://www.glassdoor.com"
_BASE_FR = "https://www.glassdoor.fr"

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

# Glassdoor location IDs (IC…) pour les principales villes françaises.
# Obtenu via /findPopularLocationAjax.htm?term=<city>
_CITY_IDS: dict[str, int] = {
    "paris": 1131050,
    "lyon": 1131051,
    "marseille": 1131052,
    "toulouse": 1131061,
    "bordeaux": 1131046,
    "nantes": 1131057,
    "strasbourg": 1131060,
    "rennes": 1131059,
    "montpellier": 1131056,
    "lille": 3061391,
    "nice": 1131058,
    "grenoble": 1131053,
    "rouen": 1131055,
    "toulon": 1131062,
    "metz": 1131054,
    "nancy": 1131048,
    "aix-en-provence": 1131045,
    "brest": 1131047,
    "amiens": 1131044,
    "caen": 3061399,
    "clermont-ferrand": 1131049,
    "dijon": 4965,
    "reims": 4952,
    "angers": 4966,
    "le-havre": 4967,
    "villeurbanne": 4963,
    "perpignan": 4964,
    "besancon": 4962,
    "tours": 4968,
}


def _slugify(text: str) -> str:
    """Lowercase, remove accents, replace spaces with dashes."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower().replace(" ", "-")


@register_scraper
class GlassdoorScraper(BaseScraper):
    name = "glassdoor"
    base_url = _BASE_FR

    def build_search_url(self, query: SearchQuery) -> str:
        city_slug = _slugify(query.location)
        kw_slug = _slugify(query.keywords)
        city_len = len(city_slug)
        kw_len = len(kw_slug)
        loc_id = _CITY_IDS.get(city_slug)
        ic_part = f"_IC{loc_id}" if loc_id else ""
        return (
            f"{_BASE}/Job/{city_slug}-{kw_slug}-jobs"
            f"-SRCH_IL.0,{city_len}{ic_part}"
            f"_KO{city_len + 1},{city_len + 1 + kw_len}.htm"
        )

    async def search(self, query: SearchQuery) -> list[JobOffer]:
        url = self.build_search_url(query)
        listings = await self._intercept_rsc(url)
        return self._parse_listings(listings)

    async def _intercept_rsc(self, url: str) -> list[dict]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(locale="fr-FR", user_agent=_UA)
            page = await ctx.new_page()

            await page.add_init_script("""
                self.__next_f_collected = [];
                self.__next_f = {
                    push: function(item) {
                        self.__next_f_collected.push(item);
                    }
                };
            """)

            try:
                await page.goto(url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            raw = await page.evaluate("""() => {
                const chunks = self.__next_f_collected || [];
                const item = chunks.find(c => {
                    if (!Array.isArray(c) || c.length < 2) return false;
                    const s = typeof c[1] === 'string' ? c[1] : '';
                    return s.includes('listingId') && s.includes('jobTitleText');
                });
                return item ? JSON.stringify(item) : null;
            }""")

            await browser.close()

        if not raw:
            return []
        return self._parse_rsc_chunk(raw)

    def _parse_rsc_chunk(self, raw: str) -> list[dict]:
        try:
            outer = json.loads(raw)
            payload_str = outer[1] if isinstance(outer, list) and len(outer) > 1 else ""
            if not isinstance(payload_str, str):
                return []
            # Format RSC wire : "5:[\"$\",\"$L4d\",null,{\"pageProps\":{...}}]..."
            # Chercher le début du JSON (après "XX:")
            colon = payload_str.find(":[")
            if colon == -1:
                colon = payload_str.find(":{")
            if colon == -1:
                return []
            decoder = json.JSONDecoder()
            data, _ = decoder.raw_decode(payload_str, colon + 1)
        except Exception:
            return []
        return self._extract_listings(data)

    def _extract_listings(self, data) -> list[dict]:
        """Cherche récursivement jobListings dans la structure JSON RSC."""
        if isinstance(data, dict):
            for key in ("pageProps", "jobSearchPage", "searchResultsData"):
                if key in data:
                    result = self._extract_listings(data[key])
                    if result:
                        return result

            if "jobListings" in data:
                jl = data["jobListings"]
                if isinstance(jl, dict) and "jobListings" in jl:
                    return jl["jobListings"]
                if isinstance(jl, list):
                    return jl

            for v in data.values():
                result = self._extract_listings(v)
                if result:
                    return result

        if isinstance(data, list):
            # RSC element format: ["$", "$L4d", null, {props}] — descend into all items
            for item in data:
                if isinstance(item, (dict, list)):
                    result = self._extract_listings(item)
                    if result:
                        return result
            # Check if this list itself is a job listings array
            if data and isinstance(data[0], dict):
                first = data[0]
                if "jobview" in first or "listingId" in str(first)[:200]:
                    return data

        return []

    def _parse_listings(self, listings: list[dict]) -> list[JobOffer]:
        jobs: list[JobOffer] = []
        seen: set[str] = set()

        for item in listings:
            jv = item.get("jobview", item)
            header = jv.get("header", {})
            job_info = jv.get("job", {})

            title = job_info.get("jobTitleText", "")
            if not title:
                continue

            job_id = job_info.get("listingId")
            if not job_id:
                continue
            job_url = f"{_BASE_FR}/job-listing/j?jl={job_id}"
            if job_url in seen:
                continue
            seen.add(job_url)

            company = header.get("employerNameFromSearch") or "Non précisé"
            location_name = header.get("locationName") or "Non précisé"

            salary = None
            pay_period = header.get("payPeriod")
            adjusted = header.get("payPeriodAdjustedPay") or {}
            currency = header.get("payCurrency", "EUR")
            if pay_period and adjusted.get("p10") and adjusted.get("p90"):
                p10 = int(adjusted["p10"])
                p90 = int(adjusted["p90"])
                period_label = "an" if pay_period == "ANNUAL" else pay_period.lower()
                salary = f"{p10:,} – {p90:,} {currency}/{period_label}"

            jobs.append(
                JobOffer(
                    title=title,
                    company=company,
                    location=location_name,
                    url=job_url,
                    source_site=self.name,
                    salary=salary,
                    contract_type="CDI",
                )
            )

        return jobs
