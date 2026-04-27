with deese_pro as (
    select
        id::number                                      as order_id,
        li.value:id::number                             as line_item_id,
        li.value:product_id::number                     as product_id,
        li.value:variant_id::number                     as variant_id,
        li.value:title::varchar                         as product_title,
        li.value:sku::varchar                           as sku,
        li.value:quantity::number                       as quantity,
        li.value:price_set:shop_money:amount::float     as unit_price_gbp,
        li.value:gift_card::boolean                     as is_gift_card,
        'deese_pro'                                     as store_id
    from {{ source('bronze_shopify_deese_pro', 'orders') }},
    lateral flatten(input => line_items) li
    where (_airbyte_meta:changes is null or array_size(_airbyte_meta:changes) = 0)
      and line_items is not null
),

isclinical as (
    select
        id::number                                      as order_id,
        li.value:id::number                             as line_item_id,
        li.value:product_id::number                     as product_id,
        li.value:variant_id::number                     as variant_id,
        li.value:title::varchar                         as product_title,
        li.value:sku::varchar                           as sku,
        li.value:quantity::number                       as quantity,
        li.value:price_set:shop_money:amount::float     as unit_price_gbp,
        li.value:gift_card::boolean                     as is_gift_card,
        'isclinical'                                    as store_id
    from {{ source('bronze_shopify_isclinical', 'orders') }},
    lateral flatten(input => line_items) li
    where (_airbyte_meta:changes is null or array_size(_airbyte_meta:changes) = 0)
      and line_items is not null
)

select * from deese_pro
union all
select * from isclinical
