with unioned as (
    select * from {{ ref('stg_remotive_jobs') }}
    union all by name
    select * from {{ ref('stg_arbeitnow_jobs') }}
),

cleaned as (
    select
        *,
        trim(regexp_replace(
            regexp_replace(
                replace(replace(description_html, '&nbsp;', ' '), chr(160), ' '),
                '<[^>]+>', ' ', 'g'
            ),
            '\s+', ' ', 'g'
        )) as description_text,
        lower(title) as title_lower
    from unioned
)

select
    source,
    job_id,
    title,
    company_name,
    location,
    is_remote,
    published_at,
    tags,
    description_text,
    url,
       case
        when regexp_matches(title_lower, 'intern|praktik|werkstudent|stagiaire|trainee|^stage\b|\(stage\)') then 'intern'
        when regexp_matches(title_lower, '\bjunior\b|\bjr\b|graduate') then 'junior'
        when regexp_matches(title_lower, 'senior|\bsr\b|\blead\b|principal|staff|head of') then 'senior'
        else 'unspecified'
    end as seniority,
    (
        regexp_matches(
            title_lower,
            'data (and ai )?(engineer|scien|analy|architect|warehouse|infrastructure|ops|programmer)'
            || '|data ?plat+form|data ?warehouse|databricks'
            || '|data & ml|analytics engineer|machine learning|\bml\b|mlops'
            || '|\bbi\b|business intelligence|\betl\b'
            || '|daten(analy|ingenieur|architekt|integration)'
        )
        and not regexp_matches(
            title_lower,
            'sales|datenschutz|privacy|advocaat|lawyer|legal|\bsoc\b|security'
        )
    ) as is_data_job,
            
    ingested_at
from cleaned