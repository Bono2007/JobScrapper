from abc import ABC, abstractmethod

import structlog

from src.models.job import JobOffer
from src.models.search import SearchQuery

logger = structlog.get_logger()


class BaseScraper(ABC):
    name: str = "base"
    base_url: str = ""

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[JobOffer]: ...

    @abstractmethod
    def build_search_url(self, query: SearchQuery) -> str: ...

    async def safe_search(self, query: SearchQuery) -> list[JobOffer]:
        try:
            logger.info(
                "scraper.start",
                scraper=self.name,
                keywords=query.keywords,
                location=query.location,
            )
            results = await self.search(query)
            logger.info("scraper.done", scraper=self.name, count=len(results))
            return results
        except Exception as exc:
            logger.error("scraper.failed", scraper=self.name, error=str(exc))
            return []
