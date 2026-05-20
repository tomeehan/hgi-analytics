-- Klaviyo campaign-attributed revenue rolled up to one row per campaign per
-- month. Grain: one row per campaign_id x store_id x order_month.
--
-- This is the campaign-level detail behind the CAMPAIGN REV headline in the
-- CRM KPI strip (KPI Report page 16). It does NOT re-run the 5-day-window
-- attribution: it reuses fct_klaviyo_revenue, which already attributes each
-- Placed Order to a single campaign or flow (one row per attributed order
-- event, partitioned by event_id so no order is double counted). Here we
-- simply take the campaign-attributed slice and sum revenue per campaign.
--
-- CAMPAIGN NAME
-- fct_klaviyo_revenue carries campaign_id (the Klaviyo `$campaign` key from
-- the engagement event) but not the human-facing send name. The send name is
-- NOT recoverable from BRONZE_KLAVIYO_ISCLINICAL.CAMPAIGNS: the `$campaign`
-- key on raw events does not join to CAMPAIGNS.id (0% overlap, verified
-- 2026-05-20 -- the campaigns stream and the events stream use disjoint id
-- spaces). The send name is instead carried on the engagement events
-- themselves, as the `Campaign Name` event property (one distinct name per
-- campaign_id). stg_klaviyo__events already extracts both, so we build a
-- campaign_id -> campaign_name lookup from it.
--
-- Reused by the KPI Report "Top Performing Campaigns" table (ticket 015).

with campaign_revenue as (
    select
        store_id,
        order_month,
        campaign_id,
        revenue
    from {{ ref('fct_klaviyo_revenue') }}
    where attribution_kind = 'campaign'
      and campaign_id is not null
),

-- One row per (store_id, campaign_id): the campaign send name as it appears
-- on the engagement events. campaign_name is unique per campaign_id, so
-- max() is just a deterministic pick.
campaign_names as (
    select
        store_id,
        campaign_id,
        max(campaign_name) as campaign_name
    from {{ ref('stg_klaviyo__events') }}
    where campaign_id is not null
      and campaign_name is not null
    group by store_id, campaign_id
),

aggregated as (
    select
        cr.campaign_id,
        coalesce(cn.campaign_name, cr.campaign_id) as campaign_name,
        cr.store_id,
        cr.order_month,
        sum(cr.revenue) as revenue
    from campaign_revenue cr
    left join campaign_names cn
      on  cr.store_id    = cn.store_id
      and cr.campaign_id = cn.campaign_id
    group by
        cr.campaign_id,
        coalesce(cn.campaign_name, cr.campaign_id),
        cr.store_id,
        cr.order_month
)

select * from aggregated
