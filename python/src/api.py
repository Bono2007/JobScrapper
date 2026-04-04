import asyncio
import dataclasses
import json
import sys
from collections.abc import AsyncGenerator

# Playwright requires SelectorEventLoop on Windows (ProactorEventLoop is the default
# in Python 3.12 on Windows and breaks Playwright's CDP protocol handling).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from src.db.repository import (
    clear_all_jobs,
    count_jobs_by_status,
    delete_job,
    get_all_jobs,
    get_job_by_id,
    get_sources,
    update_job_status,
)
from src.models.job import JobOffer
from src.models.status import JobStatus
from src.scrapers import registry  # noqa: F401
from src.scrapers.registry import list_scraper_names
from src.services.export_service import export_to_csv
from src.services.search_service import run_search_streaming

logger = structlog.get_logger()

app = FastAPI(title="JobScrapper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _job_to_dict(job: JobOffer) -> dict:
    d = dataclasses.asdict(job)
    d["status"] = job.status.value
    return d


@app.get("/scrapers")
def get_scrapers() -> list[str]:
    return list_scraper_names()


@app.get("/search/progress")
async def search_progress(
    keywords: str = Query(...),
    location: str = Query(...),
    radius_km: int = Query(30),
    exclude_keywords: str = Query(default=""),
    scraper_names: list[str] = Query(default=[]),
) -> StreamingResponse:
    from src.models.search import SearchQuery

    exclude = tuple(
        kw.strip().lower() for kw in exclude_keywords.split(",") if kw.strip()
    )
    query = SearchQuery(
        keywords=keywords,
        location=location,
        radius_km=radius_km,
        exclude_keywords=exclude,
    )
    selected = scraper_names if scraper_names else None

    async def event_generator() -> AsyncGenerator[str, None]:
        async for name, count, error in run_search_streaming(query, selected):
            if name == "__done__":
                payload = json.dumps({"done": True, "total": count})
            else:
                payload = json.dumps(
                    {"site": name, "count": count, "error": error, "done": False}
                )
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/jobs")
def jobs_list(
    status: str | None = None,
    source: str | None = None,
    keywords: str | None = None,
) -> list[dict]:
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide : {status}")
    else:
        status_filter = None
    jobs = get_all_jobs(
        status_filter=status_filter,
        source_filter=source,
        search_keywords=keywords,
    )
    return [_job_to_dict(j) for j in jobs]


@app.get("/jobs/{offer_id}")
def job_detail(offer_id: str) -> dict:
    job = get_job_by_id(offer_id)
    if not job:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return _job_to_dict(job)


@app.delete("/jobs/{offer_id}")
def delete_job_endpoint(offer_id: str) -> dict:
    if not delete_job(offer_id):
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return {"deleted": offer_id}


@app.patch("/jobs/{offer_id}/status")
def update_status(offer_id: str, status: str = Query(...)) -> dict:
    try:
        new_status = JobStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Statut invalide : {status}")
    if not update_job_status(offer_id, new_status):
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return {"offer_id": offer_id, "status": new_status.value}


@app.get("/stats")
def stats() -> dict:
    return count_jobs_by_status()


@app.get("/sources")
def sources() -> list[str]:
    return get_sources()


@app.get("/export")
def export_csv(
    status: str | None = None,
    source: str | None = None,
    keywords: str | None = None,
) -> Response:
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide : {status}")
    else:
        status_filter = None
    jobs = get_all_jobs(
        status_filter=status_filter,
        source_filter=source,
        search_keywords=keywords,
    )
    csv_content = export_to_csv(jobs)
    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=offres_emploi.csv"},
    )


@app.post("/admin/clear")
def admin_clear() -> dict:
    deleted = clear_all_jobs()
    return {"deleted": deleted}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
