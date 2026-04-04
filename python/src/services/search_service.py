import asyncio
from collections.abc import AsyncGenerator

import structlog

from src.db.repository import save_jobs
from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.scrapers.registry import get_all_scrapers, get_scraper
from src.services.dedup_service import deduplicate

logger = structlog.get_logger()


async def run_search_streaming(
    query: SearchQuery, scraper_names: list[str] | None = None
) -> AsyncGenerator[tuple[str, int], None]:
    """Générateur async qui yield (scraper_name, n_results) au fur et à mesure,
    puis ('__done__', total_unique) en dernier."""
    if scraper_names:
        scrapers = [s for name in scraper_names if (s := get_scraper(name))]
    else:
        scrapers = get_all_scrapers()

    if not scrapers:
        yield "__done__", 0
        return

    results_by_name: dict[str, list[JobOffer]] = {}

    async def run_one(scraper):
        jobs = await scraper.safe_search(query)
        return scraper.name, jobs

    futures = [asyncio.ensure_future(run_one(s)) for s in scrapers]
    for fut in asyncio.as_completed(futures):
        name, jobs = await fut
        results_by_name[name] = jobs
        yield name, len(jobs)

    # Post-traitement global
    all_jobs: list[JobOffer] = [j for lst in results_by_name.values() for j in lst]
    if query.exclude_keywords:
        exclude_lower = [kw.lower() for kw in query.exclude_keywords]
        all_jobs = [
            j
            for j in all_jobs
            if not any(kw in j.title.lower() for kw in exclude_lower)
        ]
    unique_jobs = deduplicate(all_jobs)
    inserted = save_jobs(unique_jobs, query)
    logger.info(
        "search.complete",
        total=len(all_jobs),
        unique=len(unique_jobs),
        inserted=inserted,
    )
    yield "__done__", len(unique_jobs)


async def run_search(
    query: SearchQuery, scraper_names: list[str] | None = None
) -> list[JobOffer]:
    if scraper_names:
        scrapers = [s for name in scraper_names if (s := get_scraper(name))]
    else:
        scrapers = get_all_scrapers()

    if not scrapers:
        logger.warning("search.no_scrapers")
        return []

    tasks = [scraper.safe_search(query) for scraper in scrapers]
    results = await asyncio.gather(*tasks)

    all_jobs: list[JobOffer] = []
    for job_list in results:
        all_jobs.extend(job_list)

    if query.exclude_keywords:
        exclude_lower = [kw.lower() for kw in query.exclude_keywords]
        all_jobs = [
            j
            for j in all_jobs
            if not any(kw in j.title.lower() for kw in exclude_lower)
        ]

    unique_jobs = deduplicate(all_jobs)
    inserted = save_jobs(unique_jobs, query)
    logger.info(
        "search.complete",
        total=len(all_jobs),
        unique=len(unique_jobs),
        inserted=inserted,
    )

    return unique_jobs
