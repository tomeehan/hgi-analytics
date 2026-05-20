-- Klaviyo events unioned across the loaded accounts (iSC, Deese PRO).
-- Per the project's multi-brand union convention
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
--
-- Engagement keys: Klaviyo email engagement events (Received / Opened /
-- Clicked Email) carry the campaign / flow / message identifiers on
-- attributes.event_properties under the keys `$campaign`, `$flow` and
-- `$message` (NOT `$campaign_id` / `$flow_id`). Placed Order events do
-- not carry those keys at all; instead they carry `$value`,
-- `$value_currency` and `OrderID`. Both sets of keys are extracted
-- here so downstream models (stg_klaviyo__placed_orders and the
-- 5-day-window attribution in fct_klaviyo_revenue) can read whichever
-- they need without re-parsing the JSON.

{% set brands = ['isclinical', 'deese_pro'] %}

with
{% for brand in brands %}
{{ brand }} as (
    select
        id::varchar                                             as event_id,
        type::varchar                                           as event_type,
        datetime::timestamp_tz                                  as occurred_at,
        attributes:value::float                                 as value,
        attributes:value_currency::varchar                      as value_currency,
        attributes:unique_id::varchar                           as unique_id,
        -- Engagement keys (present on Received / Opened / Clicked Email)
        attributes:event_properties:"$campaign"::varchar        as campaign_id,
        attributes:event_properties:"$flow"::varchar            as flow_id,
        attributes:event_properties:"$message"::varchar         as message_id,
        attributes:event_properties:"Campaign Name"::varchar    as campaign_name,
        -- Placed Order keys
        attributes:event_properties:"$value"::float             as order_value,
        attributes:event_properties:"$value_currency"::varchar  as order_currency,
        attributes:event_properties:"OrderID"::varchar          as order_id,
        relationships:profile:data:id::varchar                  as profile_id,
        relationships:metric:data:id::varchar                   as metric_id,
        '{{ brand }}'                                           as store_id
    from {{ source('bronze_klaviyo_' ~ brand, 'events') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
){% if not loop.last %},{% endif %}
{% endfor %}

select * from (
  {% for brand in brands %}
  select * from {{ brand }}
  {% if not loop.last %}union all{% endif %}
  {% endfor %}
)
