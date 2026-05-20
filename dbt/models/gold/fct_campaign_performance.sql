-- Klaviyo email engagement performance, monthly grain.
--
-- REBUILT off raw EVENTS (see stg_klaviyo__email_engagement). The
-- previous version of this model selected from stg_klaviyo__campaign_stats,
-- which reads Klaviyo's campaign_values_reports stream; that stream is
-- deliberately not synced by Airbyte (lean stream selection, see
-- CLAUDE.md / airbyte/README.md), so the model returned 0 rows.
--
-- Grain: one row per (store_id, send_month). Backs the open-rate and
-- click-rate halves of the CRM KPI strip on the iS Clinical KPI Report
-- (PDF page 16). open_rate / click_rate are per-row monthly ratios;
-- the Lightdash layer also exposes weighted ratio metrics
-- (avg_open_rate / avg_click_rate) that recompute the ratio
-- post-aggregation so a Month-filtered tile reads the exact monthly
-- figure rather than an average of per-row rates.
--
-- order_month_label mirrors fct_orders.order_month_label so the
-- dashboard's Month filter cross-applies via Lightdash's field-name
-- lookup.

with engagement as (
    select * from {{ ref('stg_klaviyo__email_engagement') }}
)

select
    engagement_id,
    store_id,
    send_month,
    delivered,
    unique_opens,
    unique_clicks,
    div0(unique_opens, delivered)  as open_rate,
    div0(unique_clicks, delivered) as click_rate
from engagement
