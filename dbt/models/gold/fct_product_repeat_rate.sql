with purchases as (
    select
        customer_id,
        product_id,
        store_id,
        count(distinct order_id)    as times_purchased
    from {{ ref('fct_product_sales') }}
    where customer_id is not null
      and product_id is not null
    group by 1, 2, 3
),

product_titles as (
    select
        product_id,
        store_id,
        max(product_title) as product_title
    from {{ ref('fct_product_sales') }}
    where product_id is not null
    group by 1, 2
)

select
    p.product_id,
    p.store_id,
    t.product_title,
    count(distinct p.customer_id)                                                   as unique_buyers,
    sum(case when p.times_purchased > 1 then 1 else 0 end)                          as repeat_buyers,
    round(
        100.0 * sum(case when p.times_purchased > 1 then 1 else 0 end)
        / nullif(count(distinct p.customer_id), 0),
        1
    )                                                                               as repeat_rate_pct
from purchases p
join product_titles t using (product_id, store_id)
group by 1, 2, 3
