---
name: add-shopify-store
description: >-
  Use when onboarding a new Shopify store into the dbt project. Trigger
  phrases: "add a new Shopify store", "onboard the <brand> store", "connect
  a new brand to dbt", "add <brand> to the Shopify union". Covers wiring a
  new BRONZE_SHOPIFY_<BRAND> schema through the Bronze source declaration,
  the manual per-store Silver staging CTEs, and the Lightdash display name.
  Gold needs no changes. Also describes the parallel pattern for a new
  Klaviyo account.
---

# Add a Shopify store to the dbt project

The project unions multiple Shopify stores with a manual CTE-per-store
pattern (NOT `dbt_utils.union_relations`). To add a store with the
lowercase slug `<new>` (e.g. `geske`), do the following. Active stores
today are `isclinical` and `deese_pro`.

## Step 1 - Declare the Bronze source

Airbyte provisions the `BRONZE_SHOPIFY_<NEW>` schema. dbt only declares it
as a source. Add a source block to `dbt/models/bronze/_sources.yml`:

```yaml
  - name: bronze_shopify_<new>
    database: HGI
    schema: BRONZE_SHOPIFY_<NEW>
    tables:
      - name: orders
      - name: customers
```

## Step 2 - Add the staging CTEs

`dbt/models/silver/stg_shopify__orders.sql` and
`dbt/models/silver/stg_shopify__customers.sql` each hold one CTE per store,
followed by a `unioned` CTE. For each of the two files:

1. Copy the existing `deese_pro` CTE verbatim.
2. Rename the CTE to `<new>`.
3. Change the `store_id` literal to `'<new>'`.
4. Change the source call to `{{ source('bronze_shopify_<new>', 'orders') }}`
   (use `'customers'` in `stg_shopify__customers.sql`).
5. Keep the Airbyte read filter exactly as the other CTEs have it:
   `where _airbyte_meta:changes is null or array_size(_airbyte_meta:changes) = 0`.
6. Extend the `unioned` CTE with `union all` then `select * from <new>`.

## Step 3 - Set the display name

If the human-readable brand name differs from the slug, extend the
`store_id` dimension `case` expression in `dbt/models/gold/_schema.yml`
(under `fct_orders` -> `store_id`) so `'<new>'` maps to the display name.
Existing mappings: `isclinical -> iS Clinical`, `deese_pro -> Deese PRO`,
`geske -> Geske`. Apply the same `case` on any other Gold model that
already surfaces `store_id` (`fct_ad_spend`, `fct_campaign_performance`,
`fct_klaviyo_revenue`, etc.) so the label stays consistent.

## Step 4 - No Gold changes needed

Gold facts and dimensions inherit the new store automatically through the
Silver union. Only the display-name `case` (Step 3) is a Gold-layer edit.

## Step 5 - Build and verify

From the `dbt/` directory:

```sh
dbt build --select stg_shopify__orders+ stg_shopify__customers+
```

Slim CI means the new store only reaches production after the change is
merged to `main` and the next scheduled daily dbt run fires.

## Parallel pattern: new Klaviyo account

A new Klaviyo account follows the same 3-schema shape: Bronze source ->
Silver CTE -> union. The difference is the Klaviyo staging models build
their per-brand CTEs with a Jinja loop, not hand-written CTEs. In
`stg_klaviyo__events.sql` (and the other `stg_klaviyo__*` models) add the
new slug to the `{% set brands = ['isclinical', 'deese_pro'] %}` list near
the top of the file, and add a `bronze_klaviyo_<new>` source block to
`_sources.yml`.
