-- Klaviyo metrics catalogue unioned across loaded accounts (iSC, Deese
-- PRO). Each Klaviyo account has its own set of metric IDs ("Placed
-- Order" has multiple distinct IDs per account across the account's
-- integrations) so we keep store_id on each row and resolve
-- attribution-relevant events by joining on (store_id, metric_id) and
-- filtering on the human-readable metric_name.
--
-- Revitalash is intentionally excluded: BRONZE_KLAVIYO_REVITALASH has
-- EVENTS materialised but the METRICS stream hasn't landed a table yet
-- (Airbyte connector partial state). Without metrics, Revitalash events
-- can't be resolved to "Placed Order", so Revitalash will contribute
-- zero to fct_klaviyo_revenue until that sync completes. Re-add to the
-- brand list below when BRONZE_KLAVIYO_REVITALASH.METRICS exists.

{% set brands = ['isclinical', 'deese_pro'] %}

with
{% for brand in brands %}
{{ brand }} as (
    select
        id::varchar                              as metric_id,
        attributes:name::varchar                 as metric_name,
        attributes:integration:name::varchar     as integration_name,
        '{{ brand }}'                            as store_id
    from {{ source('bronze_klaviyo_' ~ brand, 'metrics') }}
){% if not loop.last %},{% endif %}
{% endfor %}

select * from (
  {% for brand in brands %}
  select * from {{ brand }}
  {% if not loop.last %}union all{% endif %}
  {% endfor %}
)
