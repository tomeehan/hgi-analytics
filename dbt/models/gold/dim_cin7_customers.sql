with customers as (
    select * from {{ ref('stg_cin7__customers') }}
),

order_agg as (
    select
        customer_id,
        count(sale_id)                  as lifetime_orders,
        sum(paid_amount)                as lifetime_revenue,
        min(ordered_at)                 as first_order_at,
        max(ordered_at)                 as last_order_at,
        count(distinct channel_group)   as channels_used
    from {{ ref('stg_cin7__sales') }}
    group by customer_id
)

select
    c.customer_id,
    c.customer_name,
    c.status,
    c.currency,
    c.price_tier,
    coalesce(o.lifetime_orders, 0)      as lifetime_orders,
    coalesce(o.lifetime_revenue, 0)     as lifetime_revenue,
    o.first_order_at,
    o.last_order_at,
    coalesce(o.channels_used, 0)        as channels_used,
    case
        when coalesce(o.lifetime_orders, 0) = 0 then 'no_orders'
        when o.lifetime_orders = 1              then 'one_time'
        when o.lifetime_orders between 2 and 4  then 'occasional'
        else 'loyal'
    end                                 as customer_segment
from customers c
left join order_agg o using (customer_id)
