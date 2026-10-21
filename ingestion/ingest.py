import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import requests
import re

DB_PATH = Path("data/jobs.duckdb")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_json(url, params=None, retries=3):
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            log.warning("%s attempt %s failed: %s", url, attempt, e)
            if attempt == retries:
                raise
            time.sleep(5 * attempt)


def fetch_remotive():
    # public API only returns a handful of jobs and asks for max 4 calls/day
    data = get_json("https://remotive.com/api/remote-jobs", {"category": "data"})
    return [(str(job["id"]), job) for job in data["jobs"]]


def fetch_arbeitnow(max_pages=10):
    url = "https://www.arbeitnow.com/api/job-board-api"
    items = []
    for _ in range(max_pages):
        data = get_json(url)
        items += [(job["slug"], job) for job in data.get("data", [])]
        url = (data.get("links") or {}).get("next")
        if not url:
            break
        time.sleep(1)  # be polite
    return items


SOURCES = {
    "remotive": fetch_remotive,
    "arbeitnow": fetch_arbeitnow,
}

# Arbeitnow appends a random promo line to the end of every description
# ("Find more English Speaking Jobs..." / "Find Jobs in Germany..."),
# which changes the hash on every call. Strip it before hashing.
ARBEITNOW_FOOTER = re.compile(
    r'<p>Find (?:more )?<a href="https://www\.arbeitnow\.[^"]*">.*$',
    re.DOTALL,
)


def hash_input(source, job):
    if source == "arbeitnow" and job.get("description"):
        job = {**job, "description": ARBEITNOW_FOOTER.sub("", job["description"])}
    return json.dumps(job, sort_keys=True, ensure_ascii=False)
def to_dataframe(source, items, ingested_at):
    rows = []
    for job_id, job in items:
        payload = hash_input(source, job)
        rows.append({
            "source": source,
            "job_id": job_id,
            "payload": payload,
            "payload_hash": hashlib.md5(hash_input(source, job).encode("utf-8")).hexdigest(),
            "ingested_at": ingested_at,
        })
    return pd.DataFrame(rows).drop_duplicates(
        subset=["source", "job_id", "payload_hash"]
    )


def load(con, df):
    before = con.execute("SELECT count(*) FROM raw_jobs").fetchone()[0]
    con.register("incoming", df)
    con.execute("""
        INSERT INTO raw_jobs
        SELECT i.source, i.job_id, i.payload::JSON, i.payload_hash, i.ingested_at
        FROM incoming i
        WHERE NOT EXISTS (
            SELECT 1 FROM raw_jobs r
            WHERE r.source = i.source
              AND r.job_id = i.job_id
              AND r.payload_hash = i.payload_hash
        )
    """)
    con.unregister("incoming")
    return con.execute("SELECT count(*) FROM raw_jobs").fetchone()[0] - before


def main():
    ingested_at = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC

    DB_PATH.parent.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_jobs (
            source VARCHAR,
            job_id VARCHAR,
            payload JSON,
            payload_hash VARCHAR,
            ingested_at TIMESTAMP
        )
    """)

    for source, fetch in SOURCES.items():
        try:
            items = fetch()
        except Exception as e:
            log.error("%s failed, skipping: %s", source, e)
            continue
        inserted = load(con, to_dataframe(source, items, ingested_at))
        log.info("%s: fetched %s, inserted %s new rows", source, len(items), inserted)

    con.close()


if __name__ == "__main__":
    main()