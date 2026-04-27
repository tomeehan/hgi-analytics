with source as (
    select *,
        row_number() over (
            partition by productitemid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'product_items') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        productitemid                                       as product_item_id,
        sku,
        barcode,
        description,
        extendeddescription                                 as extended_description,
        webdescription                                      as web_description,
        webproductreference                                 as web_product_reference,
        cataloguecode                                       as catalogue_code,
        cataloguereference                                  as catalogue_reference,
        alternatereference1                                 as alternate_reference1,
        alternatereference2                                 as alternate_reference2,
        manufacturer,
        manufacturerreference                               as manufacturer_reference,
        categoryid                                          as category_id,
        productfamilyid                                     as product_family_id,
        type                                                as product_type,
        costprice                                           as cost_price,
        sellingprice                                        as selling_price,
        saleprice                                           as sale_price,
        nextprice                                           as next_price,
        decimalcostprice                                    as decimal_cost_price,
        decimalsellingprice                                 as decimal_selling_price,
        obsolete                                            as is_obsolete,
        sellable                                            as is_sellable,
        stocked                                             as is_stocked,
        created                           as created_at,
        lastupdatedtimestamp              as last_updated_at
    from deduped
)

select * from renamed
