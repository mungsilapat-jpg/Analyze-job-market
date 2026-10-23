import duckdb

con = duckdb.connect("data/jobs.duckdb")

print("Jobs per source")
print(con.sql("""
    SELECT source, count(*) AS total,
           count(*) FILTER (WHERE is_data_job) AS data_jobs
    FROM stg_jobs
    GROUP BY source
"""))

print("Seniority (data jobs only)")
print(con.sql("""
    SELECT seniority, count(*) AS n
    FROM stg_jobs
    WHERE is_data_job
    GROUP BY 1 ORDER BY 2 DESC
"""))

print("Sample data job titles")
print(con.sql("""
    SELECT title, seniority
    FROM stg_jobs
    WHERE is_data_job
    ORDER BY random()
    LIMIT 20
"""))



print("Has 'data' in title but NOT flagged (check for misses)")
print(con.sql("""
    SELECT title
    FROM stg_jobs
    WHERE NOT is_data_job
      AND regexp_matches(lower(title), 'data|daten|analy')
    ORDER BY random()
    LIMIT 20
"""))