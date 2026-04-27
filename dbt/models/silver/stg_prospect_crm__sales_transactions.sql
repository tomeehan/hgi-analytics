with source as (
    select *,
        row_number() over (
            partition by id
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'sales_transactions') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        id                                                  as transaction_id,
        ledger                                              as sales_ledger_id,
        ordernumber                                         as order_number,
        invoicenumber                                       as invoice_number,
        productitemid                                       as product_item_id,
        linenumber                                          as line_number,
        orderquantity                                       as qty_ordered,
        invoicequantity                                     as qty_invoiced,
        quantitydelivered                                   as qty_delivered,
        price,
        linevalue                                           as line_value,
        grossvalue                                          as gross_value,
        basevalue                                           as base_value,
        basegrossvalue                                      as base_gross_value,
        costvalue                                           as cost_value,
        costprice                                           as cost_price,
        marginvalue                                         as margin_value,
        marginpercent                                       as margin_percent,
        discountrate                                        as discount_rate,
        currencycode                                        as currency_code,
        transactiontype                                     as transaction_type,
        statusflag                                          as status_flag,
        warehousecode                                       as warehouse_code,
        departmentcode                                      as department_code,
        productdescription                                  as product_description,
        transactiondate                   as transacted_at,
        date_trunc('month', transactiondate)
                                                            as transaction_month,
        orderdate                         as ordered_at,
        invoicedate                       as invoiced_at,
        deliverydate                      as delivered_at
    from deduped
)

select * from renamed
