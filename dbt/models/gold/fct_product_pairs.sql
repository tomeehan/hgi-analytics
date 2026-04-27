with line_items as (
    select order_id, product_id, product_title
    from {{ ref('stg_shopify__order_line_items') }}
    where not coalesce(is_gift_card, false)
),

pairs as (
    select
        a.order_id,
        a.product_id        as product_a_id,
        a.product_title     as product_a,
        b.product_id        as product_b_id,
        b.product_title     as product_b
    from line_items a
    join line_items b
        on  a.order_id   = b.order_id
        and a.product_id < b.product_id
)

select
    product_a_id,
    product_a,
    product_b_id,
    product_b,
    count(distinct order_id)    as orders_together
from pairs
group by 1, 2, 3, 4
