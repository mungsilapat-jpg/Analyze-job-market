import json
import os

import duckdb

con = duckdb.connect(os.environ.get("JOBS_DB", "data/jobs.duckdb"))

for source in ["remotive", "arbeitnow"]:
    rows = con.execute("""
        SELECT job_id, payload FROM (
            SELECT job_id, payload,
                   row_number() OVER (PARTITION BY job_id ORDER BY ingested_at DESC) AS rn,
                   count(*) OVER (PARTITION BY job_id) AS n
            FROM raw_jobs
            WHERE source = ?
        )
        WHERE n > 1 AND rn <= 2
        ORDER BY job_id, rn
        LIMIT 6
    """, [source]).fetchall()

    pairs = {}
    for job_id, payload in rows:
        pairs.setdefault(job_id, []).append(json.loads(payload))

    print(f"===== {source}")
    for job_id, versions in pairs.items():
        if len(versions) < 2:
            continue
        new, old = versions[0], versions[1]
        diff = [k for k in set(new) | set(old) if new.get(k) != old.get(k)]
        print(job_id, "->", diff)
        for k in diff:
            a, b = str(old.get(k)), str(new.get(k))
            pos = len(os.path.commonprefix([a, b]))
            print(f"   {k} old: {a[max(0, pos - 30):pos + 60]!r}")
            print(f"   {k} new: {b[max(0, pos - 30):pos + 60]!r}")