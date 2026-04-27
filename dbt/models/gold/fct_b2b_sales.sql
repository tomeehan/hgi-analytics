{{ config(materialized='table') }}

with b2b_ledgers as (
    select
        sales_ledger_id,
        customer_name,
        country,
        currency_code   as ledger_currency_code,
        credit_limit
    from {{ ref('stg_prospect_crm__sales_ledgers') }}
    where is_b2c = false
),

transactions as (
    select * from {{ ref('stg_prospect_crm__sales_transactions') }}
),

orders as (
    select
        order_number,
        platform,
        source_channel,
        order_status,
        delivery_country,
        delivery_postcode,
        customer_reference,
        ordered_at,
        order_month
    from {{ ref('stg_prospect_crm__sales_orders') }}
),

products as (
    select
        product_item_id,
        sku,
        description     as product_description_canonical,
        manufacturer,
        category_id,
        product_family_id,
        product_type
    from {{ ref('stg_prospect_crm__product_items') }}
),

joined as (
    select
        t.transaction_id,
        l.sales_ledger_id,
        l.customer_name,
        l.country,
        l.credit_limit,

        t.order_number,
        coalesce(o.ordered_at, t.ordered_at)                    as ordered_at,
        coalesce(o.order_month, date_trunc('month', t.ordered_at))
                                                                as order_month,
        o.platform,
        o.source_channel,
        o.order_status,
        o.delivery_country,
        o.delivery_postcode,

        t.invoice_number,
        t.product_item_id,
        p.sku,
        coalesce(p.product_description_canonical, t.product_description)
                                                                as product_description,
        p.manufacturer,
        p.category_id,
        p.product_family_id,
        p.product_type,

        t.qty_ordered,
        t.qty_invoiced,
        t.qty_delivered,
        t.line_value,
        t.gross_value,
        t.cost_value,
        t.cost_price,
        t.margin_value,
        t.margin_percent,
        t.discount_rate,
        t.currency_code,

        t.transaction_type,
        t.warehouse_code,
        t.transacted_at,
        t.transaction_month,
        t.invoiced_at,
        t.delivered_at
    from transactions t
    inner join b2b_ledgers l on l.sales_ledger_id = t.sales_ledger_id
    left join orders     o on o.order_number = t.order_number
    left join products   p on p.product_item_id = t.product_item_id
)

select * from joined
