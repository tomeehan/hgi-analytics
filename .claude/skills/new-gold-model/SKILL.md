---
name: new-gold-model
description: >-
  Use when scaffolding a new Gold-layer dbt model with the project's
  conventions baked in. Trigger phrases: "create a new fct_ model", "add a
  Gold dimension", "build a new fact table", "new dim_ model", "add a Gold
  model". Covers the SQL house style, the boolean-to-integer cast rule, the
  store_id join discipline, and the _schema.yml block (tests plus Lightdash
  meta) the new model needs.
---

# Scaffold a new Gold model

Gold models live in `dbt/models/gold/`, prefixed `fct_` for facts and
`dim_` for dimensions. Lightdash reads from Gold.

## Conventions to follow

- Gold models are materialised as tables (set globally in
  `dbt_project.yml`). No per-model config block is needed unless overriding.
- Read upstream Silver models via `{{ ref('stg_...') }}`. Gold must NEVER
  read a `BRONZE_*` source directly, and must never write to a `BRONZE_*`
  schema (Bronze is immutable and Airbyte-owned).
- SQL style: lowercase keywords, 4-space indentation, trailing commas,
  Snowflake `::type` casts, CTEs in semantic order (inputs first, then
  transformations, then a final CTE), ending with `select * from final`
  (or `select * from <last_cte>`).
- Boolean flags that will be aggregated with `SUM` must be cast to integer.
  Snowflake cannot `SUM` a boolean:
  `(row_number() over (partition by customer_id order by created_at) = 1)::integer as is_first_order`.
- Include `store_id` in every join where both sides carry it. `store_id` is
  the universal brand key, present on every Silver and Gold table.
- Use `coalesce(<agg>, 0)` on left-joined aggregates.

## CTE skeleton (copy and adapt)

```sql
with orders as (
    select * from {{ ref('stg_shopify__orders') }}
),

refunds as (
    select * from {{ ref('stg_shopify__order_refunds') }}
),

joined as (
    select
        o.*,
        coalesce(r.refund_amount, 0)            as refund_amount,
        o.total_price - coalesce(r.refund_amount, 0) as net_sales
    from orders o
    left join refunds r
        on o.order_id = r.order_id
       and o.store_id = r.store_id
),

final as (
    select
        *,
        date_trunc('month', created_at)::date   as order_month,
        (row_number() over (
            partition by customer_id
            order by created_at
        ) = 1)::integer                         as is_first_order
    from joined
)

select * from final
```

## Register in dbt/models/gold/_schema.yml

Add a model block with a description, columns, `not_null` + `unique` on the
primary key, and `accepted_values` / range tests where sensible (integer
flags use `accepted_values: {values: [0, 1], quote: false}`; revenue
columns use `dbt_utils.accepted_range` with `min_value: 0`).

For any column a Lightdash dashboard will use, add a `meta` block: `metrics`
(with `type`, `label`, `description`, `format` like `gbp`, `round`), or
`dimension` / `additional_dimensions` (with `label`, `sql`).

For a `store_id` column, give it the display-name `case` dimension, mapping
`isclinical -> iS Clinical`, `deese_pro -> Deese PRO`, `geske -> Geske`.

```yaml
  - name: fct_<name>
    description: "One-line description of the model and its grain."
    meta:
      label: "<Display Name>"
    columns:
      - name: <pk>_id
        description: "Primary key."
        tests:
          - not_null
          - unique
        meta:
          metrics:
            <name>_count:
              type: count_distinct
              label: "<Name> Count"
              round: 0
      - name: store_id
        description: "Brand identifier."
        tests:
          - not_null
        meta:
          dimension:
            label: "Brand"
            # Keep in sync with fct_orders.store_id (CLAUDE.md -> store-name
            # display mapping).
            sql: "case ${TABLE}.store_id when 'isclinical' then 'iS Clinical' when 'deese_pro' then 'Deese PRO' when 'geske' then 'Geske' else ${TABLE}.store_id end"
      - name: total_price
        description: "Order value in GBP."
        meta:
          metrics:
            total_revenue:
              type: sum
              label: "Total Revenue"
              description: "Sum of order value for the month."
              format: "gbp"
              round: 0
```

## Build and verify

From the `dbt/` directory:

```sh
dbt build --select fct_<name>+
```

Slim CI means a new Gold model only runs in production after it is merged
to `main` and the next scheduled daily dbt run fires.
