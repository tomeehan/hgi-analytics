{{ config(materialized='table') }}

-- GA4 traffic fact at session_date x store_id x source/medium grain.
-- Pass-through over stg_google_analytics__source_medium (mirrors how
-- fct_ga_sessions wraps stg_google_analytics__sessions). This is the explore
-- the "Top traffic sources by sessions" KPI Report tile reads from, and is
-- reused by the converting-sources and PR-referrer tiles.

select * from {{ ref('stg_google_analytics__source_medium') }}
