-- Klaviyo email-list subscriber growth at monthly grain.
-- Grain: one row per (store_id, order_month).
--
-- Counts the Klaviyo "Subscribed to Email Marketing" and
-- "Unsubscribed from Email Marketing" events from the raw event stream
-- (stg_klaviyo__events) and rolls them up by calendar month. Klaviyo has
-- no native month concept, so order_month is derived here as the
-- month-truncated occurred_at, mirroring the order_month convention used
-- by the other Klaviyo Gold facts so the dashboard's filters can apply.
--
-- This model is intentionally a plain monthly fact with no trailing
-- window baked in: the 12-month rolling totals (ticket 017), the
-- monthly bar chart (ticket 018) and the monthly table (ticket 019) all
-- read from this same model. Any trailing-window logic is a query-time
-- (Lightdash chart-level filter) concern, not a model concern.
--
-- store_id keeps the model general: stg_klaviyo__events /
-- stg_klaviyo__metrics already union iSC + Deese PRO, so this rollup
-- runs per brand.

with events as (
    select
        store_id,
        metric_id,
        occurred_at
    from {{ ref('stg_klaviyo__events') }}
),

metrics as (
    select
        store_id,
        metric_id,
        metric_name
    from {{ ref('stg_klaviyo__metrics') }}
),

subscriber_events as (
    select
        e.store_id,
        date_trunc('month', e.occurred_at)::date as order_month,
        m.metric_name
    from events e
    inner join metrics m
      on  e.store_id  = m.store_id
      and e.metric_id = m.metric_id
    where m.metric_name in (
            'Subscribed to Email Marketing',
            'Unsubscribed from Email Marketing'
          )
),

monthly as (
    select
        store_id,
        order_month,
        count_if(metric_name = 'Subscribed to Email Marketing')   as subscribers_added,
        count_if(metric_name = 'Unsubscribed from Email Marketing') as unsubscribes
    from subscriber_events
    group by 1, 2
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['store_id', 'order_month']) }} as subscriber_growth_id,
        store_id,
        order_month,
        subscribers_added,
        unsubscribes,
        subscribers_added - unsubscribes as net_subscriber_change
    from monthly
)

select * from final
