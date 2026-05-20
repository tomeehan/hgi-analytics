-- Klaviyo Placed Order revenue attributed to a campaign or a flow via a
-- 5-day-window engagement join. Grain: one row per ATTRIBUTED Placed
-- Order event (orders with no qualifying email engagement in the
-- 5-day window are dropped, since they are not revenue Klaviyo claims
-- credit for).
--
-- ATTRIBUTION MODEL
-- Klaviyo's native attribution credits a Placed Order to the campaign
-- or flow of the most recent email the profile *engaged with* (opened
-- or clicked) inside a 5-day window before the order. The raw Placed
-- Order event does not carry a campaign / flow key, so we reconstruct
-- the attribution here:
--   1. Take deduped Placed Orders (stg_klaviyo__placed_orders -- one
--      event per OrderID).
--   2. For each, find that profile's email engagement events
--      (Opened Email / Clicked Email) that occurred at or before the
--      order and no earlier than 5 days before it.
--   3. Pick the single most recent qualifying engagement and inherit
--      its $campaign / $flow.
--   4. attribution_kind = 'campaign' if a $campaign is present, else
--      'flow'. Engagement events carry exactly one of the two.
-- This is a reconstruction of Klaviyo's own attribution engine, not a
-- read of it (Klaviyo's pre-aggregated *_values_reports streams are
-- deliberately not synced -- see CLAUDE.md / airbyte/README.md). A
-- residual gap of a few percent against Klaviyo's native figure is
-- expected: Klaviyo's engine has internal tie-breaks (e.g. SMS, last
-- open vs last click priority) we cannot fully observe from raw events.
--
-- Keep this model general: stg_klaviyo__events / __placed_orders /
-- __metrics already union iSC + Deese PRO, so this attribution runs
-- per store_id and downstream Klaviyo tickets (014-016) can reuse it.

with placed_orders as (
    select
        event_id,
        store_id,
        profile_id,
        occurred_at,
        order_month,
        revenue
    from {{ ref('stg_klaviyo__placed_orders') }}
),

events as (
    select * from {{ ref('stg_klaviyo__events') }}
),

metrics as (
    select store_id, metric_id, metric_name
    from {{ ref('stg_klaviyo__metrics') }}
),

-- Email engagement events that carry a campaign or flow attribution.
engagement as (
    select
        e.store_id,
        e.profile_id,
        e.occurred_at,
        e.campaign_id,
        e.flow_id
    from events e
    inner join metrics m
      on e.store_id = m.store_id
     and e.metric_id = m.metric_id
    where m.metric_name in ('Opened Email', 'Clicked Email')
      and (e.campaign_id is not null or e.flow_id is not null)
),

-- Join each order to every engagement inside the 5-day window, then
-- keep only the single most recent engagement per order.
attributed as (
    select
        o.event_id,
        o.store_id,
        o.order_month,
        o.occurred_at,
        o.revenue,
        eng.campaign_id,
        eng.flow_id,
        row_number() over (
            partition by o.event_id
            order by eng.occurred_at desc
        ) as engagement_rank
    from placed_orders o
    inner join engagement eng
      on  eng.store_id   = o.store_id
      and eng.profile_id = o.profile_id
      and eng.occurred_at <= o.occurred_at
      and eng.occurred_at >= dateadd('day', -5, o.occurred_at)
),

final as (
    select
        event_id,
        store_id,
        order_month,
        occurred_at,
        revenue,
        case
            when campaign_id is not null then 'campaign'
            else 'flow'
        end as attribution_kind,
        campaign_id,
        flow_id
    from attributed
    where engagement_rank = 1
)

select * from final
