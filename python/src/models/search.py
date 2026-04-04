from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchQuery:
    keywords: str
    location: str
    radius_km: int = 30
    contract_type: str | None = None
    max_results_per_site: int = 50
    exclude_keywords: tuple[str, ...] = field(default_factory=tuple)
