from src.models.job import JobOffer
from src.services.dedup_service import deduplicate


def _make_job(
    title: str = "CRM Manager",
    company: str = "Acme",
    location: str = "Lille",
    source: str = "test",
) -> JobOffer:
    return JobOffer(
        title=title,
        company=company,
        location=location,
        url=f"https://{source}.com/job",
        source_site=source,
    )


def test_dedup_exact_duplicates():
    jobs = [
        _make_job(source="site_a"),
        _make_job(source="site_b"),
    ]
    result = deduplicate(jobs)
    assert len(result) == 1


def test_dedup_different_jobs():
    jobs = [
        _make_job(title="CRM Manager"),
        _make_job(title="Data Analyst", company="BigCo"),
    ]
    result = deduplicate(jobs)
    assert len(result) == 2


def test_dedup_fuzzy_match():
    jobs = [
        _make_job(title="CRM Manager H/F", company="Acme Corp"),
        _make_job(title="CRM Manager (H/F)", company="Acme Corp"),
    ]
    result = deduplicate(jobs)
    assert len(result) == 1


def test_dedup_preserves_order():
    jobs = [
        _make_job(title="First Job", company="Alpha"),
        _make_job(title="Second Job", company="Beta"),
        _make_job(title="Third Job", company="Gamma"),
    ]
    result = deduplicate(jobs)
    assert len(result) == 3
    assert result[0].title == "First Job"
    assert result[2].title == "Third Job"


def test_dedup_empty_list():
    assert deduplicate([]) == []
