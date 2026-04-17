with source as (
    select * from {{ source('bronze_shopify_isclinical', 'orders') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

renamed as (
    select
        id::number                          as order_id,
        name::varchar                       as order_name,
        lower(trim(email::varchar))         as email,
        created_at::timestamp_tz            as created_at,
        processed_at::timestamp_tz          as processed_at,
        updated_at::timestamp_tz            as updated_at,
        total_price::float                  as total_price,
        subtotal_price::float               as subtotal_price,
        total_tax::float                    as total_tax,
        total_discounts::float              as total_discounts,
        currency::varchar                   as currency,
        financial_status::varchar           as financial_status,
        fulfillment_status::varchar         as fulfillment_status,
        customer:id::number                 as customer_id,
        source_name::varchar                as source_name,
        tags::varchar                       as tags,
        'isclinical'                        as store_id
    from source
)

select * from renamed
