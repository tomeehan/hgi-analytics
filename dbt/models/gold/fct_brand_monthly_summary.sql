{{ config(materialized='table') }}

-- Per-brand, per-month rollup for the KPI Report's "April at a glance"
-- table (PDF page 2). Outer-joined across Shopify (orders + revenue),
-- GA4 (sessions + revenue + transactions). A brand_axis CTE guarantees
-- every loaded brand appears as a row even when one side has no data
-- (e.g. brands without GA4 currently get null sessions / transactions).
--
-- Derived ratios are computed in the model (CVR, RPS) to avoid the
-- divide-by-the-wrong-grain problem you hit if these were defined as
-- Lightdash metrics with sql expressions over fanned-out joined rows.
--
-- The set of brands here is the union of every store_id loaded into
-- fct_orders. To add a brand, ensure it lands in fct_orders first.

with shopify as (
    select
        store_id,
        order_month,
        sum(total_price) as shopify_revenue,
        count(distinct order_id) as shopify_orders
    from {{ ref('fct_orders') }}
    group by 1, 2
),

ga_sessions as (
    select
        store_id,
        order_month,
        sum(sessions) as ga_sessions,
        sum(total_revenue) as ga_revenue
    from {{ ref('fct_ga_sessions') }}
    group by 1, 2
),

ga_transactions as (
    select
        store_id,
        order_month,
        sum(transactions) as ga_transactions
    from {{ ref('stg_google_analytics__transactions') }}
    group by 1, 2
),

-- Brand axis: every (brand, month) combination that appears in any of
-- the source models, so brands with one-sided data still render a row.
brand_axis as (
    select store_id, order_month from shopify
    union
    select store_id, order_month from ga_sessions
    union
    select store_id, order_month from ga_transactions
)

select
    a.store_id,
    a.order_month,
    coalesce(s.shopify_revenue, 0)  as shopify_revenue,
    coalesce(s.shopify_orders, 0)   as shopify_orders,
    coalesce(g.ga_sessions, 0)      as ga_sessions,
    coalesce(g.ga_revenue, 0)       as ga_revenue,
    coalesce(t.ga_transactions, 0)  as ga_transactions,
    case
        when coalesce(g.ga_sessions, 0) = 0 then null
        else (coalesce(s.shopify_orders, 0)::float
              / nullif(g.ga_sessions, 0)) * 100
    end as shopify_cvr_pct,
    case
        when coalesce(g.ga_sessions, 0) = 0 then null
        else coalesce(s.shopify_revenue, 0)::float / nullif(g.ga_sessions, 0)
    end as shopify_rps_gbp
from brand_axis a
left join shopify        s using (store_id, order_month)
left join ga_sessions    g using (store_id, order_month)
left join ga_transactions t using (store_id, order_month)
