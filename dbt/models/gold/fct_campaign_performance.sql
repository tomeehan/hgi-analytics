with stats as (
    select * from {{ ref('stg_klaviyo__campaign_stats') }}
),

campaigns as (
    select * from {{ ref('stg_klaviyo__campaigns') }}
),

joined as (
    select
        s.campaign_id,
        c.campaign_name,
        c.status,
        c.send_time,
        date_trunc('month', coalesce(c.send_time, s.stat_date::timestamp_tz))::date as send_month,
        s.stat_date,
        s.store_id,
        s.delivered,
        s.opens,
        s.unique_opens,
        s.clicks,
        s.unique_clicks,
        s.bounced,
        s.unsubscribed,
        s.revenue,
        s.spam_complaints,
        div0(s.unique_opens, s.delivered)   as open_rate,
        div0(s.unique_clicks, s.delivered)  as click_rate,
        div0(s.unsubscribed, s.delivered)   as unsubscribe_rate
    from stats s
    left join campaigns c
        on s.campaign_id = c.campaign_id
        and s.store_id = c.store_id
)

select * from joined
