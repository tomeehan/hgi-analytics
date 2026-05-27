-- Two grains live in BRONZE_SHOPIFY_*.ORDER_REFUNDS: a transactions array
-- (the money side of the refund) and a refund_line_items array (the goods
-- side). We need both per order:
--   * refund_amount   = SUM(transactions.amount where kind='refund' and
--                      status='success') = total cash returned to the
--                      customer (products + tax + shipping).
--   * refund_subtotal = SUM(refund_line_items.subtotal_set.shop_money.amount)
--                      = product portion only, the figure Shopify's strict
--                      Net Sales subtracts.
with isclinical_transactions as (
    select
        r.order_id,
        sum(t.value:amount::float) as refund_amount,
        max(r.created_at) as last_refunded_at
    from {{ source('bronze_shopify_isclinical', 'order_refunds') }} r,
         lateral flatten(input => r.transactions) t
    where lower(t.value:kind::string) = 'refund'
      and lower(t.value:status::string) = 'success'
    group by r.order_id
),

isclinical_line_items as (
    select
        r.order_id,
        sum(rli.value:subtotal_set:shop_money:amount::float) as refund_subtotal
    from {{ source('bronze_shopify_isclinical', 'order_refunds') }} r,
         lateral flatten(input => r.refund_line_items) rli
    group by r.order_id
),

isclinical as (
    select
        coalesce(t.order_id, l.order_id) as order_id,
        'isclinical' as store_id,
        coalesce(t.refund_amount, 0) as refund_amount,
        coalesce(l.refund_subtotal, 0) as refund_subtotal,
        t.last_refunded_at
    from isclinical_transactions t
    full outer join isclinical_line_items l using (order_id)
),

unioned as (
    select * from isclinical
)

select * from unioned
