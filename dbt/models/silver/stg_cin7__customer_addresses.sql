with deduped as (
    select *,
        row_number() over (
            partition by id
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_cin7', 'customers') }}
),

customers as (
    select * from deduped
    where _rn = 1
      and array_size(addresses) > 0
),

flattened as (
    select
        c.id                                            as customer_id,
        a.value:ID::varchar                             as address_id,
        a.value:City::varchar                           as city,
        a.value:Country::varchar                        as country,
        trim(a.value:Postcode::varchar)                 as postcode,
        a.value:State::varchar                          as state,
        a.value:Type::varchar                           as address_type,
        a.value:DefaultForType::boolean                 as is_default,
        regexp_substr(
            upper(trim(a.value:Postcode::varchar)), '^[A-Z]+'
        )                                               as postcode_area
    from customers c,
    lateral flatten(input => c.addresses) a
)

select * from flattened
