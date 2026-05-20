{{ config(materialized='table') }}

-- iS Clinical Google Ads search-term performance, aggregated to one row
-- per (order_month, brand_intent). Backs the KPI Report's "Paid search /
-- shopping" tile (PDF page 15: GOOGLE ADS, BRANDED VS NON-BRANDED).
--
-- The PDF panel is a "search term raw report" scoped to the top 100
-- search terms by cost for the month. We reproduce that scope here. The
-- Silver model carries one row per (search_date, search_term); we first
-- roll each search term up to the month (so a term appearing on many
-- days counts once), rank those monthly terms by cost descending, keep
-- the top 100, then aggregate to (month, brand_intent). Aggregating to
-- the (month, brand_intent) grain keeps the tile fast and additive; the
-- "% of cost" share is a within-table calculation done in Lightdash.

with search_terms as (

    select * from {{ ref('stg_google_ads__search_terms') }}

),

monthly_terms as (

    select
        order_month,
        order_month_label,
        store_id,
        brand_intent,
        search_term,
        sum(clicks)      as clicks,
        sum(cost)        as cost,
        sum(conversions) as conversions
    from search_terms
    group by
        order_month,
        order_month_label,
        store_id,
        brand_intent,
        search_term

),

top_100_per_month as (

    select *
    from monthly_terms
    qualify row_number() over (
        partition by order_month
        order by cost desc
    ) <= 100

)

select
    order_month,
    order_month_label,
    store_id,
    brand_intent,
    sum(clicks)      as clicks,
    sum(cost)        as cost,
    sum(conversions) as conversions
from top_100_per_month
group by
    order_month,
    order_month_label,
    store_id,
    brand_intent
