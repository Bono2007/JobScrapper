CREATE TABLE IF NOT EXISTS jobs (
    offer_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    url TEXT NOT NULL,
    source_site TEXT NOT NULL,
    salary TEXT,
    contract_type TEXT,
    description TEXT,
    published_date TEXT,
    scraped_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    search_keywords TEXT,
    search_location TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source_site);
CREATE INDEX IF NOT EXISTS idx_jobs_search ON jobs(search_keywords, search_location);
