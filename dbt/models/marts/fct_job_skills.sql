with jobs as (
    select
        source,
        job_id,
        lower(
            coalesce(title, '') || ' '
            || coalesce(description_text, '') || ' '
            || coalesce(array_to_string(tags, ' '), '')
        ) as search_text
    from {{ ref('stg_jobs') }}
    where is_data_job
),

skills as (
    select * from {{ ref('skills') }}
)

select
    j.source,
    j.job_id,
    s.skill,
    s.category
from jobs j
join skills s
    on regexp_matches(j.search_text, s.pattern)