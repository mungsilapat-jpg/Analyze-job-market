with latest as (
    select *
    from {{ source('raw', 'raw_jobs') }}
    where source = 'arbeitnow'
    qualify row_number() over (partition by job_id order by ingested_at desc) = 1
)

select
    'arbeitnow' as source,
    job_id,
    payload->>'title' as title,
    payload->>'company_name' as company_name,
    payload->>'location' as location,
    cast(payload->>'remote' as boolean) as is_remote,
    -- created_at is a unix timestamp in seconds
    epoch_ms(cast(payload->>'created_at' as bigint) * 1000) as published_at,
    from_json(payload->'tags', '["VARCHAR"]') as tags,
    -- drop the random promo footer
    regexp_replace(
        payload->>'description',
        '(?s)<p>Find (more )?<a href="https://www\.arbeitnow\.[^"]*">.*$',
        ''
    ) as description_html,
    payload->>'url' as url,
    ingested_at
from latest