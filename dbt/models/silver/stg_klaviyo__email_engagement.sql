-- Klaviyo email engagement, aggregated monthly off raw EVENTS.
--
-- Klaviyo's pre-aggregated reporting streams (campaign_values_reports,
-- flow_series_reports) are deliberately not synced by Airbyte's lean
-- stream selection, so the legacy stg_klaviyo__campaign_stats (which
-- reads campaign_values_reports) is empty. Open rate and click rate
-- are instead derived directly from the raw Received / Opened /
-- Clicked Email events here.
--
-- GRAIN: one row per (store_id, send_month). The CRM KPI strip needs
-- a single monthly open rate and click rate; a per-campaign grain is
-- a separate concern (tickets 015 / 016 build their own per-campaign
-- and per-flow models). send_month = the calendar month of the email
-- send, taken from the event timestamp.
--
-- DELIVERED / OPENS / CLICKS
--   delivered     = count of Received Email events in the month.
--   unique_opens  = distinct (message, profile) pairs that opened.
--   unique_clicks = distinct (message, profile) pairs that clicked.
-- Klaviyo's own open / click rate is unique opens (per message-profile)
-- divided by recipients. Counting raw Opened Email events overcounts
-- badly (multi-open inflation, Apple MPP), so we dedupe to one open
-- per (message, profile). A few-percent residual gap against Klaviyo's
-- native open rate is expected: Klaviyo has internal open-dedup and
-- bot-filtering rules we cannot fully observe from raw events. Click
-- rate, which is far less affected by MPP, reconciles near-exactly.
--
-- Engagement events carry the message id on event_properties.$message
-- (exposed as message_id by stg_klaviyo__events). Sends with no
-- $campaign are flow sends; both campaign and flow emails count
-- towards delivered, so the monthly rate reconciles to the PDF's
-- "delivered" figure across the whole email programme.

with events as (
    select * from {{ ref('stg_klaviyo__events') }}
),

metrics as (
    select store_id, metric_id, metric_name
    from {{ ref('stg_klaviyo__metrics') }}
),

-- Email engagement events resolved to a human-readable metric name.
engagement as (
    select
        e.store_id,
        m.metric_name,
        date_trunc('month', e.occurred_at)::date as send_month,
        e.message_id,
        e.profile_id
    from events e
    inner join metrics m
      on e.store_id = m.store_id
     and e.metric_id = m.metric_id
    where m.metric_name in ('Received Email', 'Opened Email', 'Clicked Email')
),

aggregated as (
    select
        store_id,
        send_month,
        count_if(metric_name = 'Received Email') as delivered,
        count(distinct case
            when metric_name = 'Opened Email'
            then message_id || '|' || profile_id
        end) as unique_opens,
        count(distinct case
            when metric_name = 'Clicked Email'
            then message_id || '|' || profile_id
        end) as unique_clicks
    from engagement
    group by store_id, send_month
)

select
    store_id || '|' || to_char(send_month, 'YYYY-MM') as engagement_id,
    store_id,
    send_month,
    delivered,
    unique_opens,
    unique_clicks
from aggregated
