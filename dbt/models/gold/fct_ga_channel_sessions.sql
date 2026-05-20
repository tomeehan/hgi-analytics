{{ config(materialized='table') }}

select * from {{ ref('stg_google_analytics__channel_sessions') }}
