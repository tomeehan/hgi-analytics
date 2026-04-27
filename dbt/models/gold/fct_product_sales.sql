with line_items as (
    select * from {{ ref('stg_shopify__order_line_items') }}
),

orders as (
    select
        order_id,
        store_id,
        customer_id,
        order_month,
        created_at,
        financial_status,
        is_first_order,
        uk_region,
        shipping_country_code
    from {{ ref('fct_orders') }}
)

select
    li.line_item_id,
    li.order_id,
    li.product_id,
    li.variant_id,
    li.product_title,
    li.sku,
    li.quantity,
    li.unit_price_gbp,
    li.quantity * li.unit_price_gbp     as line_revenue_gbp,
    li.store_id,
    o.customer_id,
    o.order_month,
    o.created_at,
    o.financial_status,
    o.is_first_order,
    o.uk_region,
    o.shipping_country_code
from line_items li
left join orders o using (order_id, store_id)
where not coalesce(li.is_gift_card, false)
