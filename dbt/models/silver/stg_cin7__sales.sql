with source as (
    select *,
        row_number() over (
            partition by saleid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_cin7', 'sale_list') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        saleid                                              as sale_id,
        customerid                                          as customer_id,
        customer                                            as customer_name,
        try_to_timestamp(orderdate)                         as ordered_at,
        date_trunc('month', try_to_timestamp(orderdate))    as order_month,
        paidamount                                          as paid_amount,
        invoiceamount                                       as invoice_amount,
        basecurrency                                        as base_currency,
        customercurrency                                    as customer_currency,
        status,
        orderstatus                                         as order_status,
        fulfilmentstatus                                    as fulfilment_status,
        sourcechannel                                       as source_channel,
        case
            when sourcechannel = 'Shopify'      then 'shopify_dtc'
            when sourcechannel = 'B2B'          then 'b2b'
            when sourcechannel = 'WooCommerce'  then 'woocommerce'
            when sourcechannel = 'Amazon_UK'    then 'amazon_uk'
            else 'other'
        end                                                 as channel_group
    from deduped
    where status not in ('VOIDED')
      and try_to_timestamp(orderdate) is not null
)

select * from renamed
