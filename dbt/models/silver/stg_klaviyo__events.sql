with isclinical as (
    select
        id::varchar                                                 as event_id,
        type::varchar                                               as event_type,
        datetime::timestamp_tz                                      as occurred_at,
        attributes:value::float                                     as value,
        attributes:value_currency::varchar                          as value_currency,
        attributes:unique_id::varchar                               as unique_id,
        attributes:event_properties:"$campaign_id"::varchar         as campaign_id,
        attributes:event_properties:"$flow_id"::varchar             as flow_id,
        attributes:event_properties:"$message_id"::varchar          as message_id,
        relationships:profile:data:id::varchar                      as profile_id,
        'isclinical'                                                as store_id
    from {{ source('bronze_klaviyo_isclinical', 'events') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

deese_pro as (
    select
        id::varchar                                                 as event_id,
        type::varchar                                               as event_type,
        datetime::timestamp_tz                                      as occurred_at,
        attributes:value::float                                     as value,
        attributes:value_currency::varchar                          as value_currency,
        attributes:unique_id::varchar                               as unique_id,
        attributes:event_properties:"$campaign_id"::varchar         as campaign_id,
        attributes:event_properties:"$flow_id"::varchar             as flow_id,
        attributes:event_properties:"$message_id"::varchar          as message_id,
        relationships:profile:data:id::varchar                      as profile_id,
        'deese_pro'                                                 as store_id
    from {{ source('bronze_klaviyo_deese_pro', 'events') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

harper_grace as (
    select
        id::varchar                                                 as event_id,
        type::varchar                                               as event_type,
        datetime::timestamp_tz                                      as occurred_at,
        attributes:value::float                                     as value,
        attributes:value_currency::varchar                          as value_currency,
        attributes:unique_id::varchar                               as unique_id,
        attributes:event_properties:"$campaign_id"::varchar         as campaign_id,
        attributes:event_properties:"$flow_id"::varchar             as flow_id,
        attributes:event_properties:"$message_id"::varchar          as message_id,
        relationships:profile:data:id::varchar                      as profile_id,
        'harper_grace'                                              as store_id
    from {{ source('bronze_klaviyo_harper_grace', 'events') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

unioned as (
    select * from isclinical
    union all
    select * from deese_pro
    union all
    select * from harper_grace
)

select * from unioned
