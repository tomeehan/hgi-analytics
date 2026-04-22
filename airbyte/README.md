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

### Prospect CRM

Custom connector — source is `source-prospect-crm` (Python CDK, built from
`airbyte/source-prospect-crm/`). Docker image:
`ghcr.io/tomeehan/hgi-analytics/source-prospect-crm:latest` (built by the
`connector_prospect_crm.yml` GitHub Actions workflow on every push to `main`).

To register in Airbyte UI: **Settings → Custom connectors → Add a custom source**,
set the Docker image name above, click **Save**, then create a connection as
usual. API key is in 1Password under _Prospect CRM → API Key_.

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
2. Add Shopify and Klaviyo sources in the Airbyte UI with credentials from 1Password.
3. Create connections pointing at the new Bronze schemas with the sync schedule above.
4. Document the new connections in the tables above.
5. Follow the dbt steps in the root `CLAUDE.md` to add the new sources to `_sources.yml` and the Silver union models.
