-- if an API breaks or changes shape we'd suddenly see very few data jobs
select count(*) as data_jobs
from {{ ref('stg_jobs') }}
where is_data_job
having count(*) < 50