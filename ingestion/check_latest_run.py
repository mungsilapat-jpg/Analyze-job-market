import duckdb

con = duckdb.connect("data/jobs.duckdb")

print(con.sql("""
    SELECT
        r.source,
        count(*) FILTER (WHERE p.job_id IS NOT NULL) AS new_versions,
        count(*) FILTER (WHERE p.job_id IS NULL) AS new_jobs
    FROM raw_jobs r
    LEFT JOIN (
        SELECT DISTINCT source, job_id, ingested_at FROM raw_jobs
    ) p
        ON p.source = r.source
       AND p.job_id = r.job_id
       AND p.ingested_at < r.ingested_at
    WHERE r.ingested_at = (
        SELECT max(ingested_at) FROM raw_jobs x WHERE x.source = r.source
    )
    GROUP BY r.source
"""))