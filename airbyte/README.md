# Airbyte

Airbyte is self-hosted on Fly.io (`hgi-airbyte`, region `lhr`) and handles
ELT from Shopify and Klaviyo into Snowflake Bronze schemas.

**Connection configs are not in Git** — they live in Airbyte's internal Postgres
on the Fly.io volume. If the volume is ever lost, connections must be
manually recreated from the documentation below.

## Destination

| Field | Value |
|-------|-------|
| Type | Snowflake |
| Host | `<account>.snowflakecomputing.com` |
| Role | `LOADER` |
| Warehouse | `HGI_WH` |
| Database | `HGI` |
| Username | `airbyte_user` |

Password is stored in 1Password and entered directly in the Airbyte UI.

## Connections

One connection per source (store / Klaviyo account). Each writes to its own
`BRONZE_*` schema.

### Shopify

| Store | Destination schema | Streams |
|-------|---------------------|---------|
| isClinical | `BRONZE_SHOPIFY_ISCLINICAL` | _to document_ |
| Geske | `BRONZE_SHOPIFY_GESKE` | _to document_ |
| Deese Pro | `BRONZE_SHOPIFY_DEESE_PRO` | _to document_ |

Typical streams: `orders`, `customers`, `products`, `product_variants`,
`order_line_items`, `abandoned_checkouts`, `transactions`, `metafields`.
Sync mode: incremental where supported; full refresh for small reference tables.

### Klaviyo

| Account | Destination schema | Streams |
|---------|---------------------|---------|
| isClinical | `BRONZE_KLAVIYO_ISCLINICAL` | _to document_ |
| Geske | `BRONZE_KLAVIYO_GESKE` | _to document_ |
| Deese Pro | `BRONZE_KLAVIYO_DEESE_PRO` | _to document_ |

Typical streams: `campaigns`, `events`, `profiles`, `flows`, `lists`,
`list_members`, `metrics`.

## Sync schedule

| Stream group | Frequency | Sync type |
|--------------|-----------|-----------|
| Shopify `orders`, `transactions` | 1h | Incremental |
| Shopify `customers` | 6h | Incremental |
| Shopify `products`, `product_variants` | 6h | Full refresh |
| Klaviyo `events` | 1h | Incremental |
| Klaviyo `campaigns`, `flows`, `metrics` | 6h | Full refresh |
| Klaviyo `profiles` | 24h | Incremental |

## Adding a new store

1. Create new `BRONZE_SHOPIFY_<BRAND>` and `BRONZE_KLAVIYO_<BRAND>` schemas in Snowflake.
2. Add Shopify and Klaviyo sources in the Airbyte UI with credentials from 1Password.
3. Create connections pointing at the new Bronze schemas with the sync schedule above.
4. Document the new connections in the tables above.
5. Follow the dbt steps in the root `CLAUDE.md` to add the new sources to `_sources.yml` and the Silver union models.
