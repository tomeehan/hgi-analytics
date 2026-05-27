with orders as (
    select * from {{ ref('stg_shopify__orders') }}
),

refunds as (
    select * from {{ ref('stg_shopify__order_refunds') }}
),

-- Revenue columns follow Shopify's strict chart-of-accounts.
--   gross_sales       = product price x quantity, before any discount, return,
--                       tax or shipping. Per Shopify: subtotal_price already
--                       has discounts applied, so we add total_discounts
--                       back to recover the pre-discount product subtotal.
--   net_sales         = gross_sales - discounts - returns. Returns are the
--                       product portion of refunds (refund_subtotal), not the
--                       full refund_amount, so this excludes tax/shipping on
--                       both the credit side and the debit side.
--   total_sales       = the customer-paid grand total, pre-refund. This is
--                       Shopify's total_price (= net_sales + tax + shipping).
--   total_sales_after_returns = total_sales minus the full refund_amount.
joined as (
    select
        o.*,
        coalesce(r.refund_amount, 0)                                as refund_amount,
        coalesce(r.refund_subtotal, 0)                              as refund_subtotal,
        o.subtotal_price + o.total_discounts                        as gross_sales,
        o.subtotal_price - coalesce(r.refund_subtotal, 0)           as net_sales,
        o.total_price - coalesce(r.refund_amount, 0)                as total_sales_after_returns
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
