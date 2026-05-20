with isclinical as (
    select
        id::number                          as customer_id,
        lower(trim(email::varchar))         as email,
        first_name::varchar                 as first_name,
        last_name::varchar                  as last_name,
        created_at::timestamp_tz            as created_at,
        updated_at::timestamp_tz            as updated_at,
        orders_count::number                as orders_count,
        total_spent::float                  as total_spent,
        accepts_marketing::boolean          as accepts_marketing,
        'isclinical'                        as store_id
    from {{ source('bronze_shopify_isclinical', 'customers') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

deese_pro as (
    select
        id::number                          as customer_id,
        lower(trim(email::varchar))         as email,
        first_name::varchar                 as first_name,
        last_name::varchar                  as last_name,
        created_at::timestamp_tz            as created_at,
        updated_at::timestamp_tz            as updated_at,
        orders_count::number                as orders_count,
        total_spent::float                  as total_spent,
        accepts_marketing::boolean          as accepts_marketing,
        'deese_pro'                         as store_id
    from {{ source('bronze_shopify_deese_pro', 'customers') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

unioned as (
    select * from isclinical
    union all
    select * from deese_pro
)

select * from unioned
