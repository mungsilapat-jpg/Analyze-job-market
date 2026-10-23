import duckdb

con = duckdb.connect("data/jobs.duckdb")

print("Top skills across all data jobs")
print(con.sql("""
    SELECT skill, count(*) AS jobs,
           round(100.0 * count(*) / (SELECT count(*) FROM stg_jobs WHERE is_data_job), 1) AS pct
    FROM fct_job_skills
    GROUP BY skill
    ORDER BY jobs DESC
    LIMIT 15
"""))

print("Data jobs with no skill found")
print(con.sql("""
    SELECT count(*) AS jobs_without_skills
    FROM stg_jobs s
    WHERE is_data_job
      AND NOT EXISTS (
          SELECT 1 FROM fct_job_skills f
          WHERE f.source = s.source AND f.job_id = s.job_id
      )
"""))

print("Weekly trend sample")
print(con.sql("""
    SELECT * FROM mart_skill_trends
    WHERE skill IN ('sql', 'python', 'spark', 'dbt', 'airflow')
    ORDER BY week_start DESC, job_count DESC
    LIMIT 20
"""))