-- fails if nothing has been ingested in the last 2 days (ingested_at is UTC)
select max(ingested_at) as last_ingested
from {{ source('raw', 'raw_jobs') }}
having max(ingested_at) < timezone('UTC', now()) - interval 2 day