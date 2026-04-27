with source as (
    select *,
        row_number() over (
            partition by contactid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'contacts') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        contactid                                           as contact_id,
        nullif(lower(trim(email)), '')                      as email,
        forename                                            as first_name,
        surname                                             as last_name,
        trim(coalesce(forename, '') || ' ' || coalesce(surname, ''))
                                                            as full_name,
        title,
        jobtitle                                            as job_title,
        department,
        klaviyoid                                           as klaviyo_id,
        phonenumber                                         as phone_number,
        mobilephonenumber                                   as mobile_phone,
        addressid                                           as address_id,
        mainaddressid                                       as main_address_id,
        deliveryaddressid                                   as delivery_address_id,
        divisionid                                          as division_id,
        optin                                               as opt_in,
        emailbounced                                        as email_bounced,
        created                           as created_at,
        lastupdatedtimestamp              as last_updated_at
    from deduped
)

select * from renamed
