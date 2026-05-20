-- Klaviyo "Placed Order" events, deduplicated to one row per order.
--
-- "Placed Order" is identified by joining events.metric_id to
-- stg_klaviyo__metrics.metric_id and filtering metric_name =
-- 'Placed Order'. The legacy event_type column on stg_klaviyo__events
-- is the JSON API resource type ("event") and isn't usable for this
-- filter -- Klaviyo doesn't store the event name on the event row
-- itself, only the metric_id pointer.
--
-- DEDUP (important): each Klaviyo account fires a "Placed Order" metric
-- for the SAME order from more than one integration (the native
-- Shopify integration and the server-side API both emit one). For
-- April 2026 iSC this is 2,088 raw events against 1,043 distinct
-- OrderIDs, so summing $value over the raw events double-counts
-- revenue. We keep one event per OrderID (earliest occurred_at) before
-- any revenue is summed. Events with no OrderID (rare) are kept as-is
-- since they cannot be de-duplicated against anything.
--
-- Placed Order events do NOT carry $campaign / $flow on
-- event_properties -- Klaviyo only stamps those onto email engagement
-- events. Campaign / flow attribution is therefore a downstream
-- computation (see fct_klaviyo_revenue), not a column read.

with events as (
    select * from {{ ref('stg_klaviyo__events') }}
),

metrics as (
    select store_id, metric_id, metric_name
    from {{ ref('stg_klaviyo__metrics') }}
),

placed_orders as (
    select e.*
    from events e
    inner join metrics m
      on e.store_id = m.store_id
     and e.metric_id = m.metric_id
    where m.metric_name = 'Placed Order'
),

deduped as (
    select
        *,
        row_number() over (
            partition by store_id, order_id
            order by occurred_at, event_id
        ) as order_row
    from placed_orders
),

shaped as (
    select
        event_id,
        store_id,
        profile_id,
        occurred_at,
        date_trunc('month', occurred_at)::date as order_month,
        order_id,
        order_value::float                     as revenue,
        order_currency                         as currency
    from deduped
    -- one event per (store_id, order_id); rows without an OrderID keep
    -- order_row = 1 too (each is its own partition).
    where order_row = 1
)

select * from shaped
