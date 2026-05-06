with isclinical as (
    select
        r.order_id,
        'isclinical' as store_id,
        sum(t.value:amount::float) as refund_amount,
        max(r.created_at) as last_refunded_at
    from {{ source('bronze_shopify_isclinical', 'order_refunds') }} r,
         lateral flatten(input => r.transactions) t
    where lower(t.value:kind::string) = 'refund'
      and lower(t.value:status::string) = 'success'
    group by r.order_id
),

unioned as (
    select * from isclinical
)

select * from unioned
