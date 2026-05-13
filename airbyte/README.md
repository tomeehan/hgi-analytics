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
`grant ownership ... copy current grants` line to migrate it.

The future-grants above cover incremental streams cleanly, but they do
**not** cover `full_refresh_overwrite` streams. Airbyte's Snowflake
destination loads each full-refresh sync into a staging table under
`HGI.airbyte_internal`, then runs `ALTER TABLE ... SWAP WITH` to
atomically swap the two tables' names. SWAP keeps each object's grants
attached to the object (not the name), so the live table inherits the
staging table's grants only (`OWNERSHIP -> LOADER`, no `SELECT ->
TRANSFORMER`). Future grants on the schema do not fire on SWAP-renamed
objects, so dbt loses access on every full-refresh sync. Mitigation: a
Snowflake scheduled task that re-grants SELECT to TRANSFORMER. See
"Prospect CRM > Full-refresh grants gotcha" below for a working example.

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

| Account | Destination schema | Notes |
|---------|---------------------|-------|
| isClinical | `BRONZE_KLAVIYO_ISCLINICAL` | DTC store |
| Deese Pro | `BRONZE_KLAVIYO_DEESE_PRO` | DTC store |
| Revitalash | `BRONZE_KLAVIYO_REVITALASH` | DTC store |
| Geske | `BRONZE_KLAVIYO_GESKE` | DTC store (schema only, no syncs yet) |
| Harper Grace | `BRONZE_KLAVIYO_HARPER_GRACE` | B2B / wholesale store |

Enabled streams (per connection): `profiles`, `events`, `campaigns`,
`flows`, `lists`, `metrics`, `email_templates`, `global_exclusions`.

Disabled by design: `events_detailed`, `campaigns_detailed`,
`lists_detailed`, `campaign_values_reports`. The `*_detailed` streams are
pre-joined views of their parent (events × metrics, etc.) — redundant once
you have the lean parent + the join target. `campaign_values_reports` is
the Klaviyo "reports" endpoint, which the connector hits with a 0.0s
backoff on HTTP 429 and never recovers from. See "Klaviyo connector — known
issues" below.

**Source `start_date`:** all Klaviyo sources are pinned to
`2025-01-01T00:00:00Z`. Earlier history is not analytically useful and
ballooned the `events` stream into multi-million-row backfills that
intermittently timed out. Bump it back if you need older data and accept
the long initial sync.

#### Klaviyo connector — known issues

- **Rate-limit hangs on `*_reports` streams.** The Airbyte Klaviyo source
  retries 429s with `Backing off _send(...) for 0.0s` — i.e. no backoff —
  on at least `campaign_values_reports`. This silently zeroes out a
  connection: jobs stay `running` for days while the Bronze tables collect
  no rows. Mitigation: keep the disabled-by-design list above; if a future
  upgrade re-enables one of those streams, expect the same hang. Diagnose
  via `replication-job-<id>-attempt-0` orchestrator logs grepped for
  "Backing off" and "RATE_LIMITED".
- **Recovering from a stuck `running` job.** Cancel the zombie via the
  internal API (`POST /api/v1/jobs/cancel`), then re-trigger a sync. The
  scheduler does not always auto-respawn after a cancel — fall back to
  `POST /api/public/v1/jobs` with `jobType=sync`. See "Operational
  gotchas" below for the full recipe.

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

#### Full-refresh grants gotcha

`sales_order_headers` and `sales_invoice_headers` are full-refresh, so
every sync runs `ALTER TABLE ... SWAP WITH` against `BRONZE_PROSPECT_CRM`
and strips TRANSFORMER's SELECT grant (see "Provisioning a Bronze schema"
for the mechanism). The serverless Snowflake task
`HGI.PUBLIC.REGRANT_PROSPECT_CRM_BRONZE_SELECT` re-grants SELECT every 30
minutes, which keeps dbt CI green with a worst-case 30-minute window of
broken access after a swap. The task DDL is below; recreate it if the
project is rebuilt or copy the pattern when adding a full-refresh stream
to another source.

```sql
use role accountadmin;

create or replace task HGI.PUBLIC.REGRANT_PROSPECT_CRM_BRONZE_SELECT
  user_task_managed_initial_warehouse_size = 'XSMALL'
  schedule = '30 MINUTE'
  comment = 'Re-grants SELECT to TRANSFORMER on Prospect CRM Bronze tables. Airbyte ALTER TABLE SWAP for full-refresh streams (sales_order_headers, sales_invoice_headers) strips the FUTURE GRANT each sync.'
as
  grant select on all tables in schema HGI.BRONZE_PROSPECT_CRM
    to role TRANSFORMER;

alter task HGI.PUBLIC.REGRANT_PROSPECT_CRM_BRONZE_SELECT resume;
```

To verify the task is running and recent attempts succeeded:

```sql
select name, state, error_code, scheduled_time, completed_time
from table(information_schema.task_history(
  task_name => 'REGRANT_PROSPECT_CRM_BRONZE_SELECT',
  result_limit => 5
))
order by scheduled_time desc;
```

### Meta (Facebook/Instagram Ads)

One connection per ad account, one schema per brand. Built-in **Facebook Marketing** source connector.

| Brand | Connection name | Destination schema | Schedule |
|-------|-----------------|---------------------|----------|
| iS Clinical | `Meta - iS Clinical → HGI Snowflake` | `BRONZE_META_ISCLINICAL` | 24 h |
| Deese Pro | `Meta - Deese Pro → HGI Snowflake` | `BRONZE_META_DEESE_PRO` | 24 h |
| Revitalash | `Meta - Revitalash → HGI Snowflake` | `BRONZE_META_REVITALASH` | 24 h |

Streams (all three connections share the same selection): `ad_account`, `ad_sets`, `ads`, `ad_creatives`, `ad_creatives_from_ads`, `campaigns`, `custom_conversions`, `custom_audiences`, `images`, `videos`, plus the full `ads_insights*` family (overall, age_and_gender, country, region, dma, platform_and_device, action_type, action_carousel_card, action_conversion_device, action_product_id, action_reaction, action_video_sound, action_video_type, delivery_device, delivery_platform, delivery_platform_and_device_platform, demographics_age, demographics_country, demographics_dma_region, demographics_gender). Sync mode is `incremental_deduped_history` for `ad_sets`/`ads`/`campaigns` (cursor: `updated_time`) and the `ads_insights*` family; `full_refresh_overwrite_deduped` for `ad_account`.

**Namespace setup:** `namespaceDefinition: custom_format`, `namespaceFormat: BRONZE_META_<BRAND>` per connection. Without this, all three connections fall back to the destination's default schema (`BRONZE_SHOPIFY_ISCLINICAL`) and collide on identical table names — the same trap that previously contaminated isClinical with Revitalash data. Always set the per-brand namespace before the first sync.

## Sync schedule

| Stream group | Frequency | Sync type |
|--------------|-----------|-----------|
| Shopify `orders`, `transactions` | 1h | Incremental |
| Shopify `customers` | 6h | Incremental |
| Shopify `products`, `product_variants` | 6h | Full refresh |
| Klaviyo `events` | 1h | Incremental |
| Klaviyo `campaigns`, `flows`, `metrics` | 6h | Full refresh |
| Klaviyo `profiles` | 24h | Incremental |

## Operational gotchas

### Stuck "running" jobs after a worker crash

If `airbyte-abctl-workload-launcher` restarts mid-sync (OOM, VM reboot,
node pressure), the in-flight jobs stay marked `running` in the Airbyte
metadata DB even though their pods are gone. Symptoms:

- Snowflake Bronze tables stop receiving rows for a particular source.
- Triggering a manual sync returns `409 try-again-later` ("A sync is
  already running").
- The connection still shows as `active` with a 24h schedule, but no new
  jobs appear in the public job list for days/weeks.
- Pod list shows `replication-job-<id>-attempt-0` in `Error` state with
  high age (e.g. 7d).

This bit Klaviyo for ~12 days after a worker crash on 2026-04-20: jobs
47/48/49 stuck in `running` state with 0 rows, scheduler refused to fire
new attempts. Klaviyo Bronze sat at 0 rows.

**Fix:** force-cancel the zombie jobs, then re-trigger. Airbyte will
auto-launch fresh attempts as soon as the connection is no longer
considered "running":

```bash
# 1. Get an API token (run on the VM)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/applications/token \
  -H "Content-Type: application/json" \
  -d '{"client_id":"<id>","client_secret":"<secret>","grant-type":"client_credentials"}' \
  | jq -r .access_token)
# (creds: `abctl local credentials`)

# 2. Find the zombies via the *internal* API (the public API hides them)
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/jobs/list \
  -d '{"configTypes":["sync"],"configId":"<connectionId>","pagination":{"pageSize":3}}'

# 3. Cancel each zombie
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/jobs/cancel -d '{"id":<jobId>}'
```

The public `/api/public/v1/jobs?connectionId=<id>` endpoint **does not
return `running` jobs** — always use the internal `/api/v1/jobs/list`
when diagnosing this.

### "Successful" syncs that move 0 rows

Watch for `bytesSynced=0, recordsSynced=0` in `succeeded` jobs. Airbyte
treats a clean run with no new records as success, so a misconfigured
cursor or incomplete OAuth scope will silently land 0 rows for weeks.
Pair every connection with a Snowflake check on `last_altered` and
`row_count` of its Bronze tables.

## Adding a new store

1. Create new `BRONZE_SHOPIFY_<BRAND>` and `BRONZE_KLAVIYO_<BRAND>` schemas in Snowflake.
2. Add Shopify and Klaviyo sources in the Airbyte UI (ask Tom for credentials).
3. Create connections pointing at the new Bronze schemas with the sync schedule above.
4. Document the new connections in the tables above.
5. Follow the dbt steps in the root `CLAUDE.md` to add the new sources to `_sources.yml` and the Silver union models.
