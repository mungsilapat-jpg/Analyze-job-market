import os
import json
import duckdb

con = duckdb.connect("data/jobs.duckdb")
rows = con.execute("""
    SELECT job_id, payload
    FROM raw_jobs
    WHERE source = 'arbeitnow'
      AND job_id IN (
          SELECT job_id FROM raw_jobs
          WHERE source = 'arbeitnow'
          GROUP BY job_id
          HAVING count(*) > 1
          LIMIT 5
      )
    ORDER BY job_id
""").fetchall()

versions = {}
for job_id, payload in rows:
    versions.setdefault(job_id, []).append(json.loads(payload))



for job_id, (a, b, *_) in versions.items():
    da, db = a["description"], b["description"]
    pos = len(os.path.commonprefix([da, db]))
    print(job_id)
    print("   length:", len(da), "vs", len(db), "| differs at:", pos)
    print("   A:", repr(da[pos - 40:pos + 80]))
    print("   B:", repr(db[pos - 40:pos + 80]))