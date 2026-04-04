import csv
import io

from src.models.job import JobOffer
from src.models.status import JobStatus
from src.services.export_service import export_to_csv


def test_export_csv_headers():
    result = export_to_csv([])
    content = result.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(content))
    headers = next(reader)
    assert "title" in headers
    assert "company" in headers
    assert "url" in headers
    assert "status" in headers


def test_export_csv_content():
    jobs = [
        JobOffer(
            title="CRM Manager",
            company="Acme",
            location="Lille",
            url="https://example.com/1",
            source_site="indeed",
            salary="45k",
            status=JobStatus.INTERESTED,
        ),
    ]
    result = export_to_csv(jobs)
    content = result.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["title"] == "CRM Manager"
    assert rows[0]["company"] == "Acme"
    assert rows[0]["status"] == "interested"
    assert rows[0]["salary"] == "45k"


def test_export_csv_bom():
    result = export_to_csv([])
    assert result.startswith("\ufeff")
