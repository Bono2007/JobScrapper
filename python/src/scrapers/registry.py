from src.scrapers.base import BaseScraper

_registry: dict[str, type[BaseScraper]] = {}


def register_scraper(cls: type[BaseScraper]) -> type[BaseScraper]:
    _registry[cls.name] = cls
    return cls


def get_all_scrapers() -> list[BaseScraper]:
    _ensure_loaded()
    return [cls() for cls in _registry.values()]


def get_scraper(name: str) -> BaseScraper | None:
    _ensure_loaded()
    cls = _registry.get(name)
    return cls() if cls else None


def list_scraper_names() -> list[str]:
    _ensure_loaded()
    return sorted(_registry.keys())


_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if not _loaded:
        _loaded = True
        import src.scrapers.registry_loader  # noqa: F401
