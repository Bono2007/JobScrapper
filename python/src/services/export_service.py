import csv
import io

from src.models.job import JobOffer

CSV_COLUMNS = [
    "title",
    "company",
    "location",
    "salary",
    "contract_type",
    "source_site",
    "url",
    "published_date",
    "status",
]


def export_to_csv(jobs: list[JobOffer]) -> str:
    output = io.StringIO()
    output.write("\ufeff")  # BOM UTF-8 pour Excel
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for job in jobs:
        writer.writerow(
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary": job.salary or "",
                "contract_type": job.contract_type or "",
                "source_site": job.source_site,
                "url": job.url,
                "published_date": job.published_date or "",
                "status": job.status.value,
            }
        )
    return output.getvalue()
