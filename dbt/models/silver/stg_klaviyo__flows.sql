-- Klaviyo flows catalogue unioned across the loaded accounts (iSC,
-- Deese PRO). Per the project's multi-brand union convention
-- (CLAUDE.md -> Multi-brand Shopify/Klaviyo union) we use explicit
-- per-brand CTEs rather than dbt_utils.union_relations; each brand
-- reads from its own BRONZE_KLAVIYO_<BRAND>.FLOWS and stamps a literal
-- store_id.
--
-- A Klaviyo "flow" is an automation (Welcome Series, Abandoned
-- Checkout, Abandoned Cart, etc.) as opposed to a one-off campaign
-- send. The `id` on the flows stream matches the `$flow` key carried
-- on email engagement events (Opened / Clicked Email), so this model
-- is the flow-id -> flow-name lookup for fct_klaviyo_flow_revenue.
--
-- Harper Grace is intentionally excluded: its Klaviyo connector is
-- declared but writes no destination tables yet (airbyte/README.md).
-- Re-add a harper_grace CTE when BRONZE_KLAVIYO_HARPER_GRACE.FLOWS
-- materialises.

{% set brands = ['isclinical', 'deese_pro'] %}

with
{% for brand in brands %}
{{ brand }} as (
    select
        id::varchar                   as flow_id,
        attributes:name::varchar      as flow_name,
        attributes:status::varchar    as flow_status,
        '{{ brand }}'                 as store_id
    from {{ source('bronze_klaviyo_' ~ brand, 'flows') }}
){% if not loop.last %},{% endif %}
{% endfor %}

select * from (
  {% for brand in brands %}
  select * from {{ brand }}
  {% if not loop.last %}union all{% endif %}
  {% endfor %}
)
