with source as (
    select *,
        row_number() over (
            partition by addressid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'addresses') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        addressid                                           as address_id,
        country,
        postcode,
        outcode,
        postcoderegion                                      as postcode_region,
        postcodetype                                        as postcode_type,
        regionnumber                                        as region_number,
        addressline1                                        as address_line1,
        addressline2                                        as address_line2,
        addressline3                                        as address_line3,
        addressline4                                        as address_line4,
        addressline5                                        as address_line5,
        latitude,
        longitude,
        created                           as created_at,
        lastupdatedtimestamp              as last_updated_at
    from deduped
)

select * from renamed
