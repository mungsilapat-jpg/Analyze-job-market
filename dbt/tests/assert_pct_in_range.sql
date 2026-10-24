select *
from {{ ref('mart_skill_trends') }}
where pct_of_jobs < 0 or pct_of_jobs > 100