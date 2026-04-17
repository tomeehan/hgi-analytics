with campaigns as (
    select * from {{ ref('stg_klaviyo__campaigns') }}
    where channel = 'email'
)

select
    campaign_id,
    campaign_name,
    status,
    channel,
    send_time,
    created_at,
    updated_at,
    store_id
from campaigns
