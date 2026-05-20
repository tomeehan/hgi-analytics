# hgi-analytics

Analytics platform for Harper Grace International — consolidates data from
multiple Shopify stores and Klaviyo accounts into Snowflake, transforms it with
dbt, and serves dashboards via Lightdash.

## Stack

| Tool | Role | Hosting |
|------|------|---------|
| Shopify | Source — 4+ stores (isClinical, Geske, Deese Pro, Revitalash; more anticipated) | SaaS |
| Klaviyo | Source — 3+ accounts, paired 1:1 with Shopify stores | SaaS |
| Cin7 Core | Source — inventory, sales orders, customers, products (formerly DEAR Systems) | SaaS |
| Prospect CRM | Source — CRM (contacts, companies, leads, sales orders/invoices, transactions) — Connector Builder declarative YAML (`airbyte/source-prospect-crm/manifest.yaml`) | SaaS (OData v1 API at `crm-odata-v1.prospect365.com`) |
| Meta (Facebook Marketing) | Source — paid ads insights (`ad_account`, `ad_sets`, `ads`, `campaigns`, `ads_insights*` family). One ad account per brand (iS Clinical, Deese Pro, Revitalash) | SaaS |
| Airbyte | ELT — extracts from sources, writes raw into Snowflake Bronze | Self-hosted on a Hetzner Cloud VM (`hgi-airbyte`, Falkenstein `fsn1`), installed via `abctl` |
| Snowflake | Data warehouse | AWS `eu-west-2`, Standard edition |
| dbt Core | Transformations (Bronze → Silver → Gold → Metrics) | Local + GitHub Actions |
| Lightdash | BI / dashboards, reads the dbt project directly | Self-hosted on Hetzner Cloud (`hgi-lightdash`, `cpx22` in `fsn1`); served by Caddy with auto Let's Encrypt TLS at `lightdash.hgi.tomeehan.net` |
| Neon | Lightdash metadata Postgres (users, dashboards, saved queries) | Managed (`Lightdash` project in org `Harper grace`, region `aws-eu-west-2`) |
| GitHub Actions | dbt CI on PRs + scheduled daily production dbt runs | SaaS |
| Slack | Airbyte + dbt failure alerts | SaaS |

Snowflake is the only managed-only dependency — no BI/ingestion lock-in.

## CLIs

| CLI | Purpose |
|-----|---------|
| `basecamp` (via the `basecamp` skill) | Read/update tickets on the Data Engineering board |
| `hcloud` | Provision + manage Hetzner Cloud servers (`hgi-airbyte`, `hgi-lightdash`) — context `harper-grace` (project `14181772`) |
| `abctl` | Airbyte self-hosted install / lifecycle (run on the Hetzner VM via SSH) |
| `neonctl` | Manage Neon Postgres (Lightdash metadata DB) — org `Harper grace` (`org-bold-mouse-74970166`) |
| `ssh` | Operate the Hetzner VMs (reboot, log into `abctl`, inspect Docker / the k3d cluster) |
| `dbt` (with `dbt-snowflake` adapter) | Run/test/build models — always invoked from inside `dbt/` |
| `gh` | GitHub repo, PRs, Actions, secrets |
| `snow` (Snowflake CLI) | Ad-hoc SQL against Snowflake — two profiles: `hgi` (DBT_USER/TRANSFORMER, default) and `hgi-admin` (TOMEEHAN/ACCOUNTADMIN, for schema/grant work). Config at `~/.snowflake/config.toml`. |
| Snowflake Snowsight (web UI) | Ad-hoc SQL, credit/cost monitoring, role grants |

Prefer the dedicated CLIs over raw API calls (e.g. `gh` not cURL; `basecamp` not the Basecamp REST API).

## High-level architecture

```
Shopify stores ──┐
                 ├──▶ Airbyte ──▶ Snowflake BRONZE ──▶ dbt SILVER ──▶ dbt GOLD ──▶ Lightdash
Klaviyo accounts ┘                (raw, per-source)    (cleaned,         (facts &
                                                       unioned)          dimensions)
```

- **Bronze** — raw, untouched Airbyte output. One schema per source: `BRONZE_SHOPIFY_<BRAND>`, `BRONZE_KLAVIYO_<BRAND>`, `BRONZE_META_<BRAND>`, `BRONZE_CIN7`, `BRONZE_PROSPECT_CRM`. Only Airbyte writes here.
- **Silver** — cleaned, typed, unioned across brands. Shopify/Klaviyo tables carry a `store_id` column; Cin7 tables use `channel_group`. Multi-brand Shopify/Klaviyo unions are done manually (CTEs + `union all`), not via `dbt_utils.union_relations`.
- **Gold** — business-facing facts & dims. Lightdash reads from here:
  - `fct_orders` / `dim_customers` — Shopify orders & customers (isClinical + Deese Pro; grows as stores are added)
  - `fct_cin7_sales` / `dim_cin7_customers` — Cin7 sales & customers across all channels (Shopify DTC, B2B, WooCommerce, Amazon UK); 165K+ sales, 9-year history
  - `fct_campaign_performance` / `dim_campaigns` — Klaviyo email campaigns
  - `fct_product_sales` — Shopify order line items (LATERAL FLATTEN on LINE_ITEMS JSON array), joined to order context; includes `uk_region`, `line_revenue_gbp`
  - `fct_product_pairs` — cross-sell pairs (products bought together in the same order)
  - `fct_product_repeat_rate` — per-product repeat purchase rate
- **Metrics** — pre-aggregated tables for dashboard speed.

## Snowflake layout

- **Database:** `HGI`
- **Compute warehouse:** `HGI_WH` (X-SMALL, `AUTO_SUSPEND = 60`, `AUTO_RESUME = TRUE`)
- **Schemas:** `BRONZE_SHOPIFY_<BRAND>` · `BRONZE_KLAVIYO_<BRAND>` · `BRONZE_META_<BRAND>` · `BRONZE_CIN7` · `BRONZE_PROSPECT_CRM` · `SILVER` · `GOLD` · `METRICS`

Roles & service accounts:

| Role | User | Access |
|------|------|--------|
| `LOADER` | `airbyte_user` | Read/write all `BRONZE_*` schemas (including `BRONZE_CIN7`) |
| `TRANSFORMER` | `dbt_user` | Read all Bronze, write `SILVER`/`GOLD`/`METRICS` |
| `REPORTER` | `lightdash_user` | Read-only on `SILVER`/`GOLD`/`METRICS` |
| `ANALYST` | humans | Same as `REPORTER` (+ optional Silver read) |

## Repo structure

```
hgi-analytics/
├── bin/setup             one-shot bootstrap for a fresh checkout (mac + linux): venv, dbt deps, scaffolds profiles.yml + .env
├── airbyte/              connection config docs only (no code; configs live in Airbyte UI / on the Hetzner VM's disk)
├── dbt/                  the dbt project
│   ├── dbt_project.yml · packages.yml · profiles.yml (gitignored)
│   ├── models/
│   │   ├── bronze/       _sources.yml (declares Bronze schemas as dbt sources)
│   │   ├── silver/       stg_* models
│   │   └── gold/         fct_*, dim_*
│   └── tests/            (macros/ and a metrics/ layer will be added when needed)
├── lightdash/            Lightdash content-as-code + deployment notes
│   ├── charts/           chart YAML (dashboards-as-code; `lightdash download`/`upload`)
│   ├── dashboards/       dashboard YAML, one file per dashboard (slug-named)
│   └── migrations/       frozen legacy API scripts (audit history; do not extend)
└── .github/workflows/
    ├── dbt_ci.yml        runs on PRs — `state:modified+` slim CI
    ├── dbt_run.yml       scheduled daily production build + Slack on failure
    └── lightdash_deploy.yml  on push to main: `lightdash deploy` + `lightdash upload` (content)
```

## Conventions

- **Model prefixes** — `stg_` (Silver staging), `fct_` (Gold fact), `dim_` (Gold dimension).
- **Multi-brand Shopify/Klaviyo union** — staging models use a manual CTE-per-store pattern (`with isclinical as (...), deese_pro as (...), unioned as (select * from isclinical union all select * from deese_pro)`). **Adding a new Shopify store:**
  1. Create `BRONZE_SHOPIFY_<NEW>` schema (Airbyte provisions this).
  2. Add `bronze_shopify_<new>` source to `dbt/models/bronze/_sources.yml`.
  3. Add a new CTE to `stg_shopify__orders` and `stg_shopify__customers` with `store_id = '<new>'`, and add to the `unioned` CTE.
  Gold and Lightdash require no changes.
- **Cin7 deduplication** — `BRONZE_CIN7.SALE_LIST` and `BRONZE_CIN7.CUSTOMERS` contain ~36× duplicate rows from Airbyte incremental inserts. Silver models deduplicate via `row_number() over (partition by <pk> order by _airbyte_extracted_at desc) = 1` before any transformation.
- **`is_first_order` is an integer (0/1), not boolean** — Gold models cast the boolean expression to `::integer` so that `SUM(is_first_order)` works in Snowflake (Snowflake cannot SUM a boolean directly).
- **Airbyte Shopify connections** — four stores are connected; two are active in dbt, two are pending first-sync:
  - `isclinical-store` → `BRONZE_SHOPIFY_ISCLINICAL` (active in Silver/Gold as `store_id = 'isclinical'`)
  - `deese-pro` → `BRONZE_SHOPIFY_DEESE_PRO` (active in Silver/Gold as `store_id = 'deese_pro'`)
  - `revitalash-co-uk.myshopify.com` → `BRONZE_SHOPIFY_REVITALASH` (active in Silver/Gold as `store_id = 'revitalash'`; 4,734 orders, 76,730 customers)
  - Geske → `BRONZE_SHOPIFY_GESKE` (schema created, no data yet)
  - `BRONZE_KLAVIYO_REVITALASH` and `BRONZE_KLAVIYO_GESKE` schemas also exist (empty).
- **Meta (Facebook Marketing) connections** — three connections, one per ad account, all active on a 24h schedule:
  - `Meta - iS Clinical → HGI Snowflake` → `BRONZE_META_ISCLINICAL`
  - `Meta - Deese Pro → HGI Snowflake` → `BRONZE_META_DEESE_PRO`
  - `Meta - Revitalash → HGI Snowflake` → `BRONZE_META_REVITALASH`
  - All three use `namespaceDefinition: custom_format` with a per-brand `namespaceFormat`. Without that, Airbyte falls back to the destination's default schema (`BRONZE_SHOPIFY_ISCLINICAL`) and the three Meta connections collide on identical table names. Meta schemas are LOADER-owned (mirrors the Prospect CRM ownership pattern).
- **Klaviyo accounts** — five Klaviyo connections; four actively syncing:
  - `BRONZE_KLAVIYO_ISCLINICAL` (DTC) — active, populated.
  - `BRONZE_KLAVIYO_DEESE_PRO` (DTC) — active, populated.
  - `BRONZE_KLAVIYO_REVITALASH` (DTC) — active, populated.
  - `BRONZE_KLAVIYO_HARPER_GRACE` (B2B / wholesale) — active connection, source emits records but no destination tables get written; under investigation.
  - `BRONZE_KLAVIYO_GESKE` — schema exists, no sync configured yet.
  - All sources pinned to `start_date = 2024-07-01`; lean stream selection (no `*_detailed`, no `campaign_values_reports`) — see `airbyte/README.md` for the rationale and the recovery playbook for stuck `running` jobs.
- **Revitalash Bronze contamination — resolved** — prior to the namespace fix, the Revitalash Airbyte connection had written 4,727 orders and 76,724 customers into `BRONZE_SHOPIFY_ISCLINICAL`. These were deleted after the Revitalash full refresh completed (2026-04-27). The cleanup script is `airbyte/cleanup_isclinical_contamination.sql` (audit only; DELETEs are no longer needed).
- **`store_id` is the universal brand key** — present on every Silver+ table. Use it for joins and Lightdash dashboard filters (portfolio view = unfiltered; per-brand view = filtered).
- **Store-name display mapping** — `store_id` raw values are lowercased slugs (`revitalash`, `isclinical`, `deese_pro`, `geske`). For Lightdash display, override the dimension SQL with a `case` that maps to human-readable names: `revitalash → Revitalash`, `isclinical → iS Clinical`, `deese_pro → Deese PRO`, `geske → Geske`. Currently applied on `fct_orders.store_id` (in `dbt/models/gold/_schema.yml`). Apply the same `case` on any future explore that surfaces `store_id` so the label is consistent across dashboards.
- **Group dashboard filter convention** — Lightdash dashboards that span multiple brands or months use two dashboard-level filters: a **Brand** filter on `store_id` (default disabled = "All"; enable to scope to a single brand) and a **Month** filter on `order_month` (default = the report's reference month, e.g. April 2026). Both filters cross-apply to other explores via `tileTargets` when a tile uses a different explore that exposes the same field name.
- **Email normalisation** — `LOWER(TRIM(email))` in Silver before joining Shopify customers to Klaviyo profiles.
- **Currency** — Shopify returns a per-order `currency`. Normalisation strategy (query-time vs GBP in Silver) is undecided — preserve the `currency` column everywhere until a decision is made.
- **Testing** — `not_null` + `unique` on every primary key; range tests on revenue columns.
- **Incremental sync in Airbyte** is the default; full refresh only for small reference tables (products, campaigns).
- **Prospect CRM conventions:**
  - **Email is the cross-source customer key.** `LOWER(TRIM(email))` everywhere. CRM↔Shopify isClinical email overlap is ~91% (53,905 of 59,160 CRM emails); CRM↔Deese Pro is ~30%. CRM↔Cin7 has no email link (Cin7 customer email is nested in a JSON `CONTACTS` array, not exposed at top level) — fall back to fuzzy company-name match for now.
  - **`SALES_LEDGERS` ≠ `CONTACTS`.** Ledgers are customer-account records (with email built in); contacts are individual people. The `CONTACTID` column on `SALES_LEDGERS` is unreliable (one default value across ~99% of rows) — **join on email, not ContactId**.
  - **`is_b2c` filter** — to isolate B2B-only views, filter `sales_ledgers.is_b2c = false`. ~3,000 of 63k ledgers are B2B; the remaining ~60k are consumer ledgers (CRM mirrors the full Shopify customer base, so it isn't a B2B-only silo).
  - **Klaviyo bridge** — 11,045 contacts have `klaviyo_id` populated, all distinct — usable as a direct join to Klaviyo profile data when needed.
  - **Cross-source SKU joins are deferred** — CRM `product_items.sku` does not align cleanly with Shopify SKUs and `web_product_reference` is null in samples. Build a manual mapping table when product-level analytics is needed.
  - **Account manager names are not exposed** — `accountmanagerid` is an opaque GUID; revisit if Prospect adds a users API.
  - **CRM Bronze schema is `LOADER`-owned + has a regrant task.** `BRONZE_PROSPECT_CRM` was migrated to `LOADER` ownership (the canonical pattern, see `airbyte/README.md` "Provisioning a Bronze schema"). Two streams (`sales_order_headers`, `sales_invoice_headers`) are `full_refresh_overwrite`. Airbyte writes those via `ALTER TABLE ... SWAP WITH`, which keeps grants attached to the object (not the name), so the live table loses TRANSFORMER's SELECT grant on every sync. Schema-level future grants do not refire on SWAP-renamed objects. The serverless task `HGI.PUBLIC.REGRANT_PROSPECT_CRM_BRONZE_SELECT` runs every 30 minutes to re-grant SELECT and keep dbt CI green. See `airbyte/README.md` "Full-refresh grants gotcha" for the DDL and the verification query. Any future source that adds a `full_refresh_overwrite` stream needs the same task pattern.

## Lightdash dashboards-as-code

Charts and dashboards are managed as YAML, edited locally and synced with the
Lightdash CLI (`lightdash download` / `lightdash upload`; the CLI version is
pinned in `.github/workflows/lightdash_deploy.yml`). This replaces the old
`lightdash/migrations/` approach of POSTing to the REST API.

- **Source of truth** is `lightdash/charts/<slug>.yml` and
  `lightdash/dashboards/<slug>.yml`: one file per object, named by slug. A
  `git diff` on those files is the audit trail.
- **`lightdash deploy` vs `lightdash upload`.** `deploy` only refreshes the
  semantic layer (dbt metrics and dimensions); it does not change chart or
  dashboard config. `upload` is what pushes chart and dashboard YAML.
- **SQL Runner charts are not covered** by content-as-code. If a dashboard
  has one, that tile stays UI-only.
- **`lightdash/migrations/` is frozen** legacy history. Never add to it,
  never re-run it, and ignore the retired `bin/new-lightdash-migration`
  scaffold.
- **One-time setup.** Authenticate the CLI with `lightdash login` (or the
  `LIGHTDASH_URL` / `LIGHTDASH_API_KEY` / `LIGHTDASH_PROJECT` env vars; the
  repo `.env` already holds Lightdash credentials), then
  `lightdash config set-project`. Run `lightdash install-skills` once to add
  Lightdash's editing skill for Claude Code.

### Developing a change (visible in Lightdash before merge)

A preview project lets you see the change rendered in Lightdash without
touching production dashboards. Run these from the repo root.

1. Branch off `main`.
2. `lightdash download` to refresh the local YAML from production, so you
   start editing from live state.
3. Edit the YAML for the chart(s) or dashboard(s) you are changing.
4. `lightdash lint` to validate the YAML against Lightdash's JSON schema (no
   network). Optionally `lightdash run-chart lightdash/charts/<slug>.yml` to
   confirm a chart's query still runs against the warehouse.
5. Create a preview project and push the YAML into it:

   ```sh
   lightdash start-preview --name "$(git branch --show-current)" \
     --project-dir dbt --profiles-dir dbt
   # take the preview project UUID from the printed preview URL, then:
   lightdash upload --force --validate --project <preview-uuid>
   ```

6. Open the preview URL in the browser: that is your change, live, on a
   throwaway project, with production untouched. Iterate by editing the YAML
   and re-running the `lightdash upload` command above.
7. Tear the preview down when finished:
   `lightdash stop-preview --name "$(git branch --show-current)"`.

### Shipping it (PR workflow)

8. Commit the changed `lightdash/**/*.yml` files: that diff is the review.
9. Open a PR. Never push to `main` (see the PR-only deploy convention).
10. On merge, `lightdash_deploy.yml` runs `lightdash deploy` (semantic layer)
    then `lightdash upload --force` (content), pushing the committed YAML to
    the production project. No manual post-deploy step is needed any more.
11. Verify the result via the Lightdash API once the workflow run is green.

Production content now comes from committed YAML, so the spaces holding
code-managed dashboards should be view-only for non-admins. That stops UI
edits from silently diverging from the repo; any drift surfaces in `git diff`
after the next `lightdash download`.

## Project management

Tickets live on Basecamp — use the `basecamp` skill.

- **Data Engineering board:** https://3.basecamp.com/5735756/buckets/46863097/card_tables/9778948512
  - Account ID: `5735756`
  - Project (bucket) ID: `46863097`
  - Card table ID: `9778948512`

When the user references a ticket, card, or task on this project, default to reading/updating it on this card table via the Basecamp CLI.

## Secrets & credentials

Never commit credentials. Storage locations:

| Secret | Lives in |
|--------|----------|
| dbt Snowflake password (`TRANSFORMER`) | `dbt/profiles.yml` (local, gitignored) |
| Airbyte's Snowflake password (`LOADER`), Shopify Admin tokens, Klaviyo API keys | Airbyte UI (persisted in Airbyte's internal Postgres on the Hetzner VM's disk) |
| Lightdash secret + Neon `PGCONNECTIONURI` (metadata DB) | `/opt/lightdash/.env` on the Hetzner `hgi-lightdash` server |
| Snowflake `REPORTER` password | Lightdash app DB (entered via the Lightdash UI; stored encrypted in Neon) |
| `SNOWFLAKE_ACCOUNT/USER/PASSWORD`, `SLACK_WEBHOOK_URL` | GitHub Actions secrets |
| `snow` CLI credentials (`hgi` + `hgi-admin` profiles) | `~/.snowflake/config.toml` (local, never commit) |

## Keeping this file current

CLAUDE.md is the single source of truth for how this project is set up. Keep it
accurate as the project evolves — when work in a session changes any of the
following, update the relevant section in the same session, as part of the same
change:

- A new tool, CLI, service, or hosting target is introduced (or one is removed).
- A Snowflake resource is created, renamed, or has its access model changed
  (databases, schemas, warehouses, roles, service accounts).
- A new store or Klaviyo account is onboarded — update brand lists and any
  enumerated resource names.
- Repo structure changes (new top-level dir, new workflow, dbt project moves).
- A convention is established or changed (naming, union pattern, testing rules,
  currency handling, incremental strategy).
- A secret's storage location changes.
- A decision previously marked "undecided" gets resolved (e.g. currency
  normalisation).

If something in CLAUDE.md turns out to be wrong or stale, fix it rather than
working around it. If the architecture doc and CLAUDE.md disagree, the
architecture doc wins — update CLAUDE.md to match and flag the drift.

## Operating notes

- **Run dbt from `dbt/`**, not the repo root. Typical flow: `dbt deps && dbt build --select <target>+`.
- **Bronze is immutable** — never have dbt (or anything else) write to `BRONZE_*`. If Bronze data is wrong, fix Airbyte or re-sync.
- **Slim CI** — `dbt_ci.yml` uses `state:modified+`, so a new Gold model only runs in production after it's merged to main and the next daily run fires.
- **Snowflake cost control** — keep `HGI_WH` at X-SMALL with 60s auto-suspend. Don't leave long-running Snowsight sessions idle; don't disable auto-suspend.
- **Airbyte config is not in Git** — it lives on the Hetzner VM's disk (inside Airbyte's internal Postgres, managed by the `abctl` k3d cluster). Document every connection (streams, sync mode, schedule, destination namespace) in `airbyte/README.md` so the setup can be rebuilt if the VM is lost. **Hetzner auto-backups are enabled** on `hgi-airbyte` (daily, 7-day retention) — that's the primary recovery mechanism; do not disable them.
- **Airbyte hosting: Hetzner, not Fly** — Airbyte deprecated docker-compose OSS installs in favour of `abctl` (k3d/Kubernetes). `abctl` is designed for a plain Linux VM, not for Fly.io's Firecracker Machines — running it on Fly would require Docker-in-Docker + k3d-in-DinD, which is off-road. A single Hetzner Cloud VM with `abctl local install` is Airbyte's officially recommended OSS deploy path.
- **Prefer `dbt build` over `dbt run` + `dbt test`** — `build` runs both in dependency order and stops downstream models if a test fails.
- **Lightdash charts and dashboards are managed as code.** Edit the YAML in `lightdash/charts/` and `lightdash/dashboards/`, preview the change in a Lightdash preview project, then open a PR. See the "Lightdash dashboards-as-code" section for the full develop/preview/PR workflow. Do not call the Lightdash REST API directly for chart or dashboard CRUD.
- **`lightdash/migrations/` is frozen.** Those are the legacy one-shot API scripts that pre-date content-as-code. Keep them only as audit history: never add a new migration, never re-run an existing one, and treat the retired `bin/new-lightdash-migration` scaffold as dead. New content work is a YAML diff, not a script.
