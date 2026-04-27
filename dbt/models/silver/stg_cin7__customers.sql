with source as (
    select *,
        row_number() over (
            partition by id
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_cin7', 'customers') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        id                                      as customer_id,
        name                                    as customer_name,
        status,
        currency,
        pricetier                               as price_tier,
        creditlimit                             as credit_limit,
        try_to_timestamp(lastmodifiedon)        as last_modified_at
    from deduped
)

select * from renamed
