{{ config(materialized='table') }}

with orders_daily as (
    select
        created_at::date as date,
        store_id,
        sum(total_price) as gross_sales,
        sum(net_sales) as net_sales,
        count(distinct order_id) as orders,
        sum(is_first_order) as new_customer_orders
    from {{ ref('fct_orders') }}
    where store_id = 'isclinical'
    group by 1, 2
),

spend_daily as (
    select
        spend_date as date,
        store_id,
        sum(spend) as ad_spend
    from {{ ref('fct_ad_spend') }}
    where store_id = 'isclinical'
    group by 1, 2
),

sessions_daily as (
    select
        session_date as date,
        store_id,
        sum(sessions) as sessions
    from {{ ref('fct_ga_sessions') }}
    where store_id = 'isclinical'
    group by 1, 2
),

all_dates as (
    select date, store_id from orders_daily
    union
    select date, store_id from spend_daily
    union
    select date, store_id from sessions_daily
)

select
    d.date,
    d.store_id,
    coalesce(o.gross_sales, 0) as gross_sales,
    coalesce(o.net_sales, 0) as net_sales,
    coalesce(o.orders, 0) as orders,
    coalesce(o.new_customer_orders, 0) as new_customer_orders,
    coalesce(s.ad_spend, 0) as ad_spend,
    coalesce(g.sessions, 0) as sessions
from all_dates d
left join orders_daily o using (date, store_id)
left join spend_daily s using (date, store_id)
left join sessions_daily g using (date, store_id)
