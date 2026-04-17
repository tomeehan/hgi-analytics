with customers as (
    select * from {{ ref('stg_shopify__customers') }}
),

orders as (
    select
        customer_id,
        min(created_at)         as first_order_at,
        max(created_at)         as last_order_at,
        count(*)                as lifetime_orders,
        sum(total_price)        as lifetime_revenue
    from {{ ref('stg_shopify__orders') }}
    group by 1
),

joined as (
    select
        c.customer_id,
        c.email,
        c.first_name,
        c.last_name,
        c.created_at,
        c.updated_at,
        c.orders_count,
        c.total_spent,
        c.accepts_marketing,
        c.store_id,
        o.first_order_at,
        o.last_order_at,
        o.lifetime_orders,
        o.lifetime_revenue
    from customers c
    left join orders o using (customer_id)
)

select * from joined
