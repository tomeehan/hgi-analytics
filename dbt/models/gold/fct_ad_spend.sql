{{ config(materialized='table') }}

select * from {{ ref('stg_meta__ads_spend') }}
