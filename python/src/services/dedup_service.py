from thefuzz import fuzz

from src.config import FUZZY_DEDUP_THRESHOLD
from src.models.job import JobOffer


def deduplicate(jobs: list[JobOffer]) -> list[JobOffer]:
    seen_ids: set[str] = set()
    unique: list[JobOffer] = []

    for job in jobs:
        job = job.compute_id()
        if job.offer_id in seen_ids:
            continue

        is_fuzzy_dup = False
        for existing in unique:
            score = fuzz.token_sort_ratio(
                f"{job.title} {job.company}",
                f"{existing.title} {existing.company}",
            )
            if score >= FUZZY_DEDUP_THRESHOLD:
                is_fuzzy_dup = True
                break

        if not is_fuzzy_dup:
            seen_ids.add(job.offer_id)
            unique.append(job)

    return unique
