# Schema

Source: Remotive API (`category=data`), pulled once a day.

## raw_jobs
Append-only. Every run inserts whatever the API returns, so the same
job shows up again each day until it's taken down.

- job_id INTEGER
- payload JSON
- ingested_at TIMESTAMP

## stg_jobs
One row per job (latest version by `ingested_at`).

- job_id INTEGER, unique
- title, company_name, location TEXT
- seniority TEXT — guessed from the title, so it's rough
- published_at TIMESTAMP
- description_text TEXT — HTML stripped

## fct_job_skills
job_id + skill, one row per pair.

## mart_skill_trends
week_start, skill, job_count. This is what the dashboard reads.

## Notes
- Keeping the raw JSON means I can add columns later without re-pulling.
- Skills come from `tags` and `description`. A lot of postings leave
  `tags` empty, so tags alone undercount.
- Not sure yet how to handle postings that get edited after publishing.
  For now stg just keeps the newest copy.



- Found ~150 duplicate rows in the first Arbeitnow load. New postings
shift items between pages while paginating, so the same job can appear on two pages. Now deduped within each batch before insert.