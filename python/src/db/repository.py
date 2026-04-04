import sqlite3
from pathlib import Path

from src.config import DATA_DIR, DB_PATH
from src.models.job import JobOffer
from src.models.search import SearchQuery
from src.models.status import JobStatus


def _ensure_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    schema_path = Path(__file__).parent / "schema.sql"
    conn.executescript(schema_path.read_text())
    return conn


def _row_to_job(row: sqlite3.Row) -> JobOffer:
    return JobOffer(
        offer_id=row["offer_id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        url=row["url"],
        source_site=row["source_site"],
        salary=row["salary"],
        contract_type=row["contract_type"],
        description=row["description"],
        published_date=row["published_date"],
        scraped_at=row["scraped_at"],
        status=JobStatus(row["status"]),
    )


def save_jobs(jobs: list[JobOffer], query: SearchQuery) -> int:
    conn = _ensure_db()
    inserted = 0
    try:
        for job in jobs:
            job = job.compute_id().with_scraped_at()
            try:
                conn.execute(
                    """INSERT INTO jobs
                       (offer_id, title, company, location, url, source_site,
                        salary, contract_type, description, published_date,
                        scraped_at, status, search_keywords, search_location)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        job.offer_id,
                        job.title,
                        job.company,
                        job.location,
                        job.url,
                        job.source_site,
                        job.salary,
                        job.contract_type,
                        job.description,
                        job.published_date,
                        job.scraped_at,
                        job.status.value,
                        query.keywords,
                        query.location,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                pass  # doublon, on ignore
        conn.commit()
    finally:
        conn.close()
    return inserted


def get_all_jobs(
    status_filter: JobStatus | None = None,
    source_filter: str | None = None,
    search_keywords: str | None = None,
    limit: int | None = None,
) -> list[JobOffer]:
    conn = _ensure_db()
    try:
        sql = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter.value)
        if source_filter:
            sql += " AND source_site = ?"
            params.append(source_filter)
        if search_keywords:
            sql += " AND search_keywords LIKE ?"
            params.append(f"%{search_keywords}%")
        sql += " ORDER BY scraped_at DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_job(row) for row in rows]
    finally:
        conn.close()


def get_last_search_context() -> tuple[str, str] | None:
    """Retourne (search_keywords, search_location) de la dernière recherche."""
    conn = _ensure_db()
    try:
        row = conn.execute(
            "SELECT search_keywords, search_location FROM jobs"
            " WHERE search_keywords IS NOT NULL"
            " ORDER BY scraped_at DESC LIMIT 1"
        ).fetchone()
        if row:
            return row["search_keywords"], row["search_location"]
        return None
    finally:
        conn.close()


def clear_all_jobs() -> int:
    conn = _ensure_db()
    try:
        cursor = conn.execute("DELETE FROM jobs")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def update_job_status(offer_id: str, new_status: JobStatus) -> bool:
    conn = _ensure_db()
    try:
        cursor = conn.execute(
            "UPDATE jobs SET status = ? WHERE offer_id = ?",
            (new_status.value, offer_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_job_by_id(offer_id: str) -> JobOffer | None:
    conn = _ensure_db()
    try:
        row = conn.execute(
            "SELECT * FROM jobs WHERE offer_id = ?", (offer_id,)
        ).fetchone()
        return _row_to_job(row) if row else None
    finally:
        conn.close()


def job_exists(offer_id: str) -> bool:
    conn = _ensure_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM jobs WHERE offer_id = ?", (offer_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_sources() -> list[str]:
    conn = _ensure_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_site FROM jobs ORDER BY source_site"
        ).fetchall()
        return [row["source_site"] for row in rows]
    finally:
        conn.close()


def count_jobs_by_status() -> dict[str, int]:
    conn = _ensure_db()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status"
        ).fetchall()
        return {row["status"]: row["cnt"] for row in rows}
    finally:
        conn.close()


def delete_job(offer_id: str) -> bool:
    conn = _ensure_db()
    try:
        cursor = conn.execute("DELETE FROM jobs WHERE offer_id = ?", (offer_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
