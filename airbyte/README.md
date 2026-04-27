# Airbyte

Airbyte is self-hosted on a Hetzner Cloud VM (`hgi-airbyte`, Falkenstein
`fsn1`), installed via `abctl local install` (k3d-based). It handles ELT from
Shopify and Klaviyo into Snowflake Bronze schemas.

**Connection configs are not in Git** — they live in Airbyte's internal Postgres
inside the k3d cluster on the VM's disk. **Hetzner auto-backups are enabled**
on `hgi-airbyte` (daily, 7-day retention) — restore via
`hcloud server rebuild hgi-airbyte --image <backup-id>` or the Hetzner console.
The documentation below is the fallback if both the VM and all 7 backups are
lost (unlikely).

**Host:** `colmwca.pq47939.snowflakecomputing.com` (Snowflake account URL used by the destination below).

## Destination

| Field | Value |
|-------|-------|
| Type | Snowflake |
| Host | `colmwca.pq47939.snowflakecomputing.com` |
| Role | `LOADER` |
| Warehouse | `HGI_WH` |
| Database | `HGI` |
| Username | `airbyte_user` |

The `LOADER` password is entered directly in the Airbyte UI (ask Tom).

## Provisioning a Bronze schema

Airbyte's `LOADER` role creates per-stream tables itself, but it can't create
the parent schema. Run this once per new source as `accountadmin` (via
`snow sql --connection hgi-admin`), substituting the schema name:

```sql
use role accountadmin;
create schema if not exists HGI.BRONZE_<SOURCE>;

-- Hand the schema to LOADER so it owns everything Airbyte creates.
-- This is the canonical Airbyte+Snowflake pattern and is what makes
-- TRANSFORMER's future-grants below fire reliably on full-refresh
-- streams, which drop+recreate their tables every sync.
grant ownership on schema HGI.BRONZE_<SOURCE> to role LOADER copy current grants;

grant usage on schema HGI.BRONZE_<SOURCE> to role TRANSFORMER;
grant select on all tables in schema HGI.BRONZE_<SOURCE> to role TRANSFORMER;
grant select on future tables in schema HGI.BRONZE_<SOURCE> to role TRANSFORMER;
```

If the schema already exists and is owned by `ACCOUNTADMIN`, run the same
`grant ownership ... copy current grants` line to migrate it. Without
LOADER ownership, future-grants set up by ACCOUNTADMIN can fail to apply
to tables LOADER recreates during `full_refresh_overwrite` syncs — the
new tables end up readable only by LOADER and `dbt_user` loses access.

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

### Prospect CRM

Custom connector built using the Airbyte Connector Builder (low-code declarative
YAML). The manifest lives at `airbyte/source-prospect-crm/manifest.yaml` — no
Docker image or registry needed.

To set up: open your Airbyte instance → **Builder** → **Import a YAML** → paste
the contents of `manifest.yaml` → **Publish to workspace**. Then create a
connection as usual. Ask Tom for the Prospect CRM API key.

| Destination schema | Streams | Sync mode |
|--------------------|---------|-----------|
| `BRONZE_PROSPECT_CRM` | `contacts`, `companies`, `sales_ledgers`, `leads`, `sales_transactions`, `product_items`, `addresses` | Incremental (`LastUpdatedTimestamp`) |
| `BRONZE_PROSPECT_CRM` | `sales_order_headers`, `sales_invoice_headers` | Full refresh |

Suggested schedule: 6 h for incremental streams; 24 h for full-refresh streams.

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
2. Add Shopify and Klaviyo sources in the Airbyte UI (ask Tom for credentials).
3. Create connections pointing at the new Bronze schemas with the sync schedule above.
4. Document the new connections in the tables above.
5. Follow the dbt steps in the root `CLAUDE.md` to add the new sources to `_sources.yml` and the Silver union models.
