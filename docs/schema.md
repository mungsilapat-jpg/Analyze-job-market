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

- is_data_job is a keyword match on the title. First version matched
  any "data"/"analyst" and pulled in lawyers, sales and security roles,
  so it now needs a specific role phrase and excludes a few words.
  Checked by eyeballing random samples of both flagged and unflagged
  titles. Still misses some edge cases.
- Remotive's category=data returned 0 actual data roles after
  filtering, so almost all data jobs come from Arbeitnow.
- seniority is guessed from the title. Most postings don't say, so
  "unspecified" is the biggest group.

  - Skills are regex patterns in seeds/skills.csv, matched against title +
  description + tags. Only 11 of 203 data jobs matched no skill.
- Weekly numbers for older weeks are undercounted because ingestion only
  reads the 10 newest pages. Trends need a few weeks of daily runs.