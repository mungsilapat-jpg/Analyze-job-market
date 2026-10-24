-- a job must appear once per source after picking the latest version
select source, job_id, count(*) as n
from {{ ref('stg_jobs') }}
group by source, job_id
having count(*) > 1