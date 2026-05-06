{{ config(materialized='table') }}

select * from {{ ref('stg_google_analytics__sessions') }}
