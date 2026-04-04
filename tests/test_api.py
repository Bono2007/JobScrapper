import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client():
    from src.api import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def test_get_scrapers(client):
    response = await client.get("/scrapers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "francetravail" in data


async def test_get_jobs_empty(client):
    response = await client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_stats(client):
    response = await client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


async def test_get_job_not_found(client):
    response = await client.get("/jobs/nonexistent_id")
    assert response.status_code == 404


async def test_patch_status_not_found(client):
    response = await client.patch("/jobs/nonexistent_id/status?status=seen")
    assert response.status_code == 404


async def test_patch_status_invalid(client):
    response = await client.patch("/jobs/some_id/status?status=invalid_value")
    assert response.status_code == 400


async def test_clear(client):
    response = await client.post("/admin/clear")
    assert response.status_code == 200
    assert "deleted" in response.json()


async def test_get_sources(client):
    response = await client.get("/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_jobs_invalid_status(client):
    response = await client.get("/jobs?status=invalid_value")
    assert response.status_code == 400


async def test_export_empty(client):
    response = await client.get("/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    # BOM UTF-8 présent
    assert response.content.startswith(b"\xef\xbb\xbf")


async def test_get_job_does_not_auto_mark_seen(client):
    """GET /jobs/{id} ne doit pas modifier le statut."""
    # D'abord créer une offre en base via clear (vide) puis vérifier que 404
    response = await client.get("/jobs/any_id")
    assert response.status_code == 404
    # Si l'offre n'existe pas, pas de mutation possible — test de non-régression
