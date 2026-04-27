with source as (
    select *,
        row_number() over (
            partition by ordernumber
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'sales_order_headers') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        ordernumber                                         as order_number,
        salesledgerid                                       as sales_ledger_id,
        salespersonid                                       as salesperson_id,
        divisionid                                          as division_id,
        netvalue                                            as net_value,
        taxvalue                                            as tax_value,
        grossvalue                                          as gross_value,
        basenetvalue                                        as base_net_value,
        basetaxvalue                                        as base_tax_value,
        basegrossvalue                                      as base_gross_value,
        currencycode                                        as currency_code,
        platform,
        source                                              as source_channel,
        orderstatus                                         as order_status,
        statusflag                                          as status_flag,
        customerreference                                   as customer_reference,
        alternatereference                                  as alternate_reference,
        deliveryname                                        as delivery_name,
        deliverycountry                                     as delivery_country,
        deliverypostcode                                    as delivery_postcode,
        salesordergroupcode                                 as sales_order_group_code,
        orderdate                         as ordered_at,
        date_trunc('month', orderdate)    as order_month,
        shippeddate                       as shipped_at,
        duedate                           as due_at
    from deduped
    where ordernumber is not null
)

select * from renamed
