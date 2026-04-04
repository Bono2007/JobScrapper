from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.models.status import JobStatus


def test_job_offer_is_frozen():
    job = JobOffer(
        title="CRM Manager",
        company="Acme",
        location="Lille",
        url="https://example.com/1",
        source_site="test",
    )
    try:
        job.title = "Other"
        assert False, "Should not allow mutation"
    except AttributeError:
        pass


def test_job_compute_id():
    job = JobOffer(
        title="CRM Manager",
        company="Acme",
        location="Lille",
        url="https://example.com/1",
        source_site="test",
    )
    job_with_id = job.compute_id()
    assert job_with_id.offer_id is not None
    assert len(job_with_id.offer_id) == 16
    assert job.offer_id is None  # original unchanged


def test_job_compute_id_deterministic():
    job1 = JobOffer(
        title="CRM Manager",
        company="Acme",
        location="Lille",
        url="https://a.com",
        source_site="a",
    )
    job2 = JobOffer(
        title="CRM Manager",
        company="Acme",
        location="Lille",
        url="https://b.com",
        source_site="b",
    )
    assert job1.compute_id().offer_id == job2.compute_id().offer_id


def test_job_compute_id_case_insensitive():
    job1 = JobOffer(
        title="CRM Manager",
        company="ACME",
        location="LILLE",
        url="https://a.com",
        source_site="a",
    )
    job2 = JobOffer(
        title="crm manager",
        company="acme",
        location="lille",
        url="https://b.com",
        source_site="b",
    )
    assert job1.compute_id().offer_id == job2.compute_id().offer_id


def test_job_with_status():
    job = JobOffer(
        title="Test",
        company="Co",
        location="Paris",
        url="https://x.com",
        source_site="test",
    )
    assert job.status == JobStatus.NEW
    interested = job.with_status(JobStatus.INTERESTED)
    assert interested.status == JobStatus.INTERESTED
    assert job.status == JobStatus.NEW  # original unchanged


def test_job_with_scraped_at():
    job = JobOffer(
        title="Test",
        company="Co",
        location="Paris",
        url="https://x.com",
        source_site="test",
    )
    assert job.scraped_at is None
    stamped = job.with_scraped_at()
    assert stamped.scraped_at is not None
    assert job.scraped_at is None


def test_search_query_defaults():
    q = SearchQuery(keywords="CRM Marketing", location="Lille")
    assert q.radius_km == 30
    assert q.contract_type is None
    assert q.max_results_per_site == 50


def test_job_status_values():
    assert JobStatus.NEW.value == "new"
    assert JobStatus.SEEN.value == "seen"
    assert JobStatus.INTERESTED.value == "interested"
    assert JobStatus.REJECTED.value == "rejected"
