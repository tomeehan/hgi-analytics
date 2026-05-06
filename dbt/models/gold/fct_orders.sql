with orders as (
    select * from {{ ref('stg_shopify__orders') }}
),

refunds as (
    select * from {{ ref('stg_shopify__order_refunds') }}
),

joined as (
    select
        o.*,
        coalesce(r.refund_amount, 0) as refund_amount,
        o.total_price - coalesce(r.refund_amount, 0) as net_sales
    from orders o
    left join refunds r
        on o.order_id = r.order_id
       and o.store_id = r.store_id
),

with_flags as (
    select
        *,
        date_trunc('month', created_at)::date as order_month,
        (row_number() over (
            partition by customer_id
            order by created_at
        ) = 1)::integer as is_first_order
    from joined
)

select * from with_flags
