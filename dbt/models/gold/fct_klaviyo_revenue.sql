-- Klaviyo Placed Order revenue, filtered to events that have either
-- a campaign or a flow attribution (i.e. revenue Klaviyo claims credit
-- for under its 5-day attribution window).
--
-- KNOWN GAP (2026-05-19): this model currently returns ZERO ROWS in
-- production. The Bronze Placed Order events emitted by our Klaviyo
-- ingestion DO NOT carry `$campaign_id` or `$flow_id` on
-- attributes.event_properties. Klaviyo's attribution is done in the
-- Klaviyo UI / Reports endpoints (campaign_values_reports,
-- flow_values_reports), not on the raw event payload. Our
-- campaign_values_reports stream is currently empty too — it's
-- disabled-by-design per airbyte/README.md ("Klaviyo connector — known
-- issues" hangs on the *_values_reports endpoints).
--
-- This is wired up as scaffolding so the moment attribution arrives
-- (e.g. a sibling ticket that re-enables campaign_values_reports
-- carefully, or builds attribution from a click-chain on the raw
-- events), this model + its downstream tile will start producing
-- numbers. Until then, the Combined Klaviyo Revenue tile is
-- intentionally NOT installed on the KPI Report dashboard — showing
-- £0 would be misleading.

{# Keep the SQL itself sensible so the day this lights up, it just works. #}

select
    event_id,
    store_id,
    order_month,
    occurred_at,
    revenue,
    attribution_kind,
    campaign_id,
    flow_id
from {{ ref('stg_klaviyo__placed_orders') }}
where attribution_kind in ('campaign', 'flow')
