-- Klaviyo Placed Order events with attribution kind. One row per Placed
-- Order event, retaining the campaign_id / flow_id keys so downstream
-- models can break out by attribution surface. attribution_kind is
-- derived once here so consumers don't have to repeat the case logic.
--
-- "Placed Order" is identified by joining events.metric_id to
-- stg_klaviyo__metrics.metric_id and filtering metric_name =
-- 'Placed Order'. The legacy event_type column on stg_klaviyo__events
-- is the JSON API resource type ("event") and isn't usable for this
-- filter — confusingly Klaviyo doesn't store the event name on the
-- event row itself, only the metric_id pointer.

with events as (
    select * from {{ ref('stg_klaviyo__events') }}
),

metrics as (
    select store_id, metric_id, metric_name
    from {{ ref('stg_klaviyo__metrics') }}
),

placed_orders as (
    select e.*, m.metric_name
    from events e
    inner join metrics m
      on e.store_id = m.store_id
     and e.metric_id = m.metric_id
    where m.metric_name = 'Placed Order'
),

shaped as (
    select
        event_id,
        store_id,
        occurred_at,
        date_trunc('month', occurred_at)::date as order_month,
        value::float                            as revenue,
        campaign_id,
        flow_id,
        case
            when campaign_id is not null then 'campaign'
            when flow_id is not null     then 'flow'
            else 'unattributed'
        end as attribution_kind
    from placed_orders
)

select * from shaped
