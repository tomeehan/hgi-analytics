-- Klaviyo events unioned across the loaded accounts (iSC, Deese PRO,
-- Revitalash). Per the project's multi-brand union convention
-- (CLAUDE.md → Multi-brand Shopify/Klaviyo union) we use explicit
-- per-brand CTEs rather than dbt_utils.union_relations; each brand
-- reads from its own BRONZE_KLAVIYO_<BRAND>.EVENTS, casts the
-- attribute JSON fields, and stamps a literal store_id.
--
-- Harper Grace is intentionally excluded today: the Klaviyo connector
-- is declared but does not actually write destination rows yet
-- (airbyte/README.md notes "the source emits records but no destination
-- tables get written; under investigation"), so the EVENTS table
-- doesn't exist in Snowflake. Re-add a harper_grace CTE when the
-- Airbyte gap is fixed and BRONZE_KLAVIYO_HARPER_GRACE.EVENTS materialises.

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
        relationships:metric:data:id::varchar                       as metric_id,
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
        relationships:metric:data:id::varchar                       as metric_id,
        'deese_pro'                                                 as store_id
    from {{ source('bronze_klaviyo_deese_pro', 'events') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

revitalash as (
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
        relationships:metric:data:id::varchar                       as metric_id,
        'revitalash'                                                as store_id
    from {{ source('bronze_klaviyo_revitalash', 'events') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

unioned as (
    select * from isclinical
    union all
    select * from deese_pro
    union all
    select * from revitalash
)

select * from unioned
