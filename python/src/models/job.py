from dataclasses import dataclass, replace
from datetime import datetime
from hashlib import sha256

from src.models.status import JobStatus


@dataclass(frozen=True)
class JobOffer:
    title: str
    company: str
    location: str
    url: str
    source_site: str
    salary: str | None = None
    contract_type: str | None = None
    description: str | None = None
    published_date: str | None = None
    scraped_at: str | None = None
    status: JobStatus = JobStatus.NEW
    offer_id: str | None = None

    def compute_id(self) -> "JobOffer":
        raw = f"{self.title.lower().strip()}|{self.company.lower().strip()}|{self.location.lower().strip()}"
        hash_id = sha256(raw.encode()).hexdigest()[:16]
        return replace(self, offer_id=hash_id)

    def with_status(self, new_status: JobStatus) -> "JobOffer":
        return replace(self, status=new_status)

    def with_scraped_at(self) -> "JobOffer":
        return replace(self, scraped_at=datetime.now().isoformat())
