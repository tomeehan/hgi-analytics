with source as (
    select *,
        row_number() over (
            partition by salesledgerid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'sales_ledgers') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        salesledgerid                                       as sales_ledger_id,
        nullif(lower(trim(email)), '')                      as email,
        name                                                as customer_name,
        country,
        countrycode                                         as country_code,
        postcode,
        currencycode                                        as currency_code,
        isb2c                                               as is_b2c,
        iscashaccount                                       as is_cash_account,
        customertypeid                                      as customer_type_id,
        customercode                                        as customer_code,
        balance,
        creditlimit                                         as credit_limit,
        created                           as created_at,
        lastinvoice                       as last_invoice_at,
        lastreceipt                       as last_receipt_at,
        lastupdatedtimestamp              as last_updated_at
    from deduped
)

select * from renamed
