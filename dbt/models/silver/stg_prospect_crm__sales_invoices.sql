with source as (
    select *,
        row_number() over (
            partition by invoicenumber
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'sales_invoice_headers') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        invoicenumber                                       as invoice_number,
        salesorderheaderid                                  as sales_order_header_id,
        salesledgerid                                       as sales_ledger_id,
        creditnotenumber                                    as credit_note_number,
        netvalue                                            as net_value,
        taxvalue                                            as tax_value,
        grossvalue                                          as gross_value,
        basenetvalue                                        as base_net_value,
        basetaxvalue                                        as base_tax_value,
        basegrossvalue                                      as base_gross_value,
        currencycode                                        as currency_code,
        platform,
        statusflag                                          as status_flag,
        transactiontypeid                                   as transaction_type_id,
        invoicedate                       as invoiced_at,
        date_trunc('month', invoicedate)  as invoice_month,
        duedate                           as due_at
    from deduped
    where invoicenumber is not null
)

select * from renamed
