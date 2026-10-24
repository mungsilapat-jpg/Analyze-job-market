import json
import os
import re
from collections import Counter

import duckdb

con = duckdb.connect(os.environ.get("JOBS_DB", "data/jobs.duckdb"))

# same promo footer we strip before hashing
FOOTER = re.compile(r'<p>Find (?:more )?<a href="https://www\.arbeitnow\.[^"]*">.*$', re.DOTALL)

# 1) latest run: new jobs vs new versions of jobs we already had
print(con.sql("""
    WITH latest AS (
        SELECT max(ingested_at) AS ts FROM raw_jobs WHERE source = 'arbeitnow'
    )
    SELECT
        count(*) FILTER (WHERE seen_before) AS new_versions,
        count(*) FILTER (WHERE NOT seen_before) AS new_jobs
    FROM (
        SELECT EXISTS (
            SELECT 1 FROM raw_jobs p
            WHERE p.source = r.source AND p.job_id = r.job_id
              AND p.ingested_at < r.ingested_at
        ) AS seen_before
        FROM raw_jobs r, latest
        WHERE r.source = 'arbeitnow' AND r.ingested_at = latest.ts
    )
"""))

# 2) for jobs with 2+ versions: which fields changed between the last two?
rows = con.execute("""
    SELECT job_id, payload FROM (
        SELECT job_id, payload,
               row_number() OVER (PARTITION BY job_id ORDER BY ingested_at DESC) AS rn,
               count(*) OVER (PARTITION BY job_id) AS n
        FROM raw_jobs
        WHERE source = 'arbeitnow'
    )
    WHERE n > 1 AND rn <= 2
    ORDER BY job_id, rn
""").fetchall()

pairs = {}
for job_id, payload in rows:
    job = json.loads(payload)
    if job.get("description"):
        job["description"] = FOOTER.sub("", job["description"])
    pairs.setdefault(job_id, []).append(job)

counter = Counter()
for new, old in (v for v in pairs.values() if len(v) == 2):
    diff = tuple(sorted(k for k in set(new) | set(old) if new.get(k) != old.get(k)))
    counter[diff or ("(footer only)",)] += 1

print("changed fields -> number of jobs")
for fields, n in counter.most_common():
    print(f"  {', '.join(fields)}: {n}")