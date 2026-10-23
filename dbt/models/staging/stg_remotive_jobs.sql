with latest as (
    select *
    from {{ source('raw', 'raw_jobs') }}
    where source = 'remotive'
    qualify row_number() over (partition by job_id order by ingested_at desc) = 1
)

select
    'remotive' as source,
    job_id,
    payload->>'title' as title,
    payload->>'company_name' as company_name,
    payload->>'candidate_required_location' as location,
    true as is_remote,
    cast(payload->>'publication_date' as timestamp) as published_at,
    from_json(payload->'tags', '["VARCHAR"]') as tags,
    payload->>'description' as description_html,
    payload->>'url' as url,
    ingested_at
from latest