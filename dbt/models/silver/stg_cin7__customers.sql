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
        -- CONTACTS is a JSON array; the default contact's email is the
        -- best customer-level email Cin7 exposes (~97% populated).
        lower(trim(contacts[0]:Email::string))  as email,
        status,
        currency,
        pricetier                               as price_tier,
        creditlimit                             as credit_limit,
        try_to_timestamp(lastmodifiedon)        as last_modified_at
    from deduped
)

select * from renamed
