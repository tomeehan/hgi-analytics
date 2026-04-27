with orders as (
    select * from {{ ref('stg_shopify__orders') }}
),

with_flags as (
    select
        *,
        date_trunc('month', created_at)::date as order_month,
        (row_number() over (
            partition by customer_id
            order by created_at
        ) = 1)::integer as is_first_order
    from orders
)

select * from with_flags
