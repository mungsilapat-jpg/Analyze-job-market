import duckdb

# one-off: upload the local database to MotherDuck
con = duckdb.connect("md:")
con.execute("CREATE DATABASE job_market FROM 'data/jobs.duckdb'")

print(con.sql("""
    SELECT source, count(*) AS rows
    FROM job_market.raw_jobs
    GROUP BY source
"""))