-- Klaviyo flow-attributed revenue rolled up to one row per flow per
-- month. Grain: one row per flow_id x store_id x order_month.
--
-- This is the flow-level detail behind the FLOW REV headline in the
-- CRM KPI strip (KPI Report page 16) and the flow-side companion of
-- fct_klaviyo_campaign_revenue (ticket 015). It does NOT re-run the
-- 5-day-window attribution: it reuses fct_klaviyo_revenue, which
-- already attributes each Placed Order to a single campaign or flow
-- (one row per attributed order event, partitioned by event_id so no
-- order is double counted). Here we take the flow-attributed slice and
-- sum revenue per flow.
--
-- FLOW NAME
-- fct_klaviyo_revenue carries flow_id (the Klaviyo `$flow` key from the
-- engagement event). Unlike the campaign case, `$flow` DOES join
-- cleanly to the FLOWS stream id (verified 2026-05-20: 23/23 distinct
-- event flow ids matched BRONZE_KLAVIYO_ISCLINICAL.FLOWS.id), so the
-- human-readable flow name comes from stg_klaviyo__flows, joined on
-- flow_id + store_id.
--
-- Note: a few Klaviyo flow names are not unique (e.g. a "live" and a
-- "draft" copy of "Abandoned Cart"). Grain here is flow_id, so each
-- distinct automation is its own row; the downstream table tile groups
-- by flow_name, which sums any same-named flows together.
--
-- Reused by the KPI Report "Top Performing Flows" table (ticket 016).

with flow_revenue as (
    select
        store_id,
        order_month,
        flow_id,
        revenue
    from {{ ref('fct_klaviyo_revenue') }}
    where attribution_kind = 'flow'
      and flow_id is not null
),

flow_names as (
    select
        store_id,
        flow_id,
        flow_name
    from {{ ref('stg_klaviyo__flows') }}
),

aggregated as (
    select
        fr.flow_id,
        coalesce(fn.flow_name, fr.flow_id) as flow_name,
        fr.store_id,
        fr.order_month,
        sum(fr.revenue) as revenue
    from flow_revenue fr
    left join flow_names fn
      on  fr.store_id = fn.store_id
      and fr.flow_id  = fn.flow_id
    group by
        fr.flow_id,
        coalesce(fn.flow_name, fr.flow_id),
        fr.store_id,
        fr.order_month
)

select * from aggregated
