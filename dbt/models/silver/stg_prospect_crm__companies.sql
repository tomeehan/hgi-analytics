with source as (
    select *,
        row_number() over (
            partition by companyid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'companies') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        companyid                                           as company_id,
        name                                                as company_name,
        accountmanagerid                                    as account_manager_id,
        statusflag                                          as status_flag,
        source                                              as source_channel,
        typeid                                              as type_id,
        alternatereference                                  as alternate_reference,
        created                           as created_at,
        firstorder                        as first_order_at,
        lapsed                            as lapsed_at,
        unlapsed                          as unlapsed_at,
        lastupdatedtimestamp              as last_updated_at
    from deduped
)

select * from renamed
