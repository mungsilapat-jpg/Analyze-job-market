with job_weeks as (
    select
        source,
        job_id,
        cast(date_trunc('week', published_at) as date) as week_start
    from {{ ref('stg_jobs') }}
    where is_data_job
),

weekly_totals as (
    select week_start, count(*) as total_jobs
    from job_weeks
    group by 1
)

select
    w.week_start,
    f.skill,
    f.category,
    count(*) as job_count,
    t.total_jobs,
    round(100.0 * count(*) / t.total_jobs, 1) as pct_of_jobs
from {{ ref('fct_job_skills') }} f
join job_weeks w using (source, job_id)
join weekly_totals t using (week_start)
group by w.week_start, f.skill, f.category, t.total_jobs
order by w.week_start, job_count desc