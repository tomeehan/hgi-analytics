# hgi-analytics

Analytics platform for Harper Grace International — consolidates data from
multiple Shopify stores and Klaviyo accounts into Snowflake, transforms it with
dbt, and serves dashboards via Lightdash.

## Stack

| Tool | Role | Hosting |
|------|------|---------|
| Shopify | Source — 3+ stores (isClinical, Geske, Deese Pro; more anticipated) | SaaS |
| Klaviyo | Source — 3+ accounts, paired 1:1 with Shopify stores | SaaS |
| Cin7 Core | Source — inventory, sales orders, customers, products (formerly DEAR Systems) | SaaS |
| Prospect CRM | Source — CRM (contacts, companies, leads, sales orders/invoices, transactions) — custom connector (`airbyte/source-prospect-crm/`) | SaaS (OData v1 API at `crm-odata-v1.prospect365.com`) |
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

- **Bronze** — raw, untouched Airbyte output. One schema per source: `BRONZE_SHOPIFY_<BRAND>`, `BRONZE_KLAVIYO_<BRAND>`. Only Airbyte writes here.
- **Silver** — cleaned, typed, unioned across brands. Every table has a `store_id` column. Built via `dbt_utils.union_relations`.
- **Gold** — business-facing facts & dims (`fct_orders`, `dim_customers`, `fct_campaign_events`, etc.). Lightdash reads from here.
- **Metrics** — pre-aggregated tables for dashboard speed.

## Snowflake layout

- **Database:** `HGI`
- **Compute warehouse:** `HGI_WH` (X-SMALL, `AUTO_SUSPEND = 60`, `AUTO_RESUME = TRUE`)
- **Schemas:** `BRONZE_SHOPIFY_<BRAND>` · `BRONZE_KLAVIYO_<BRAND>` · `BRONZE_CIN7` · `BRONZE_PROSPECT_CRM` · `SILVER` · `GOLD` · `METRICS`

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
├── airbyte/              connection config docs only (no code; configs live in Airbyte UI / on the Hetzner VM's disk)
├── dbt/                  the dbt project
│   ├── dbt_project.yml · packages.yml · profiles.yml (gitignored)
│   ├── models/
│   │   ├── bronze/       _sources.yml (declares Bronze schemas as dbt sources)
│   │   ├── silver/       stg_* models
│   │   └── gold/         fct_*, dim_*
│   └── tests/            (macros/ and a metrics/ layer will be added when needed)
├── lightdash/            deployment notes (live config lives on the Hetzner server at /opt/lightdash/)
└── .github/workflows/
    ├── dbt_ci.yml        runs on PRs — `state:modified+` slim CI
    └── dbt_run.yml       scheduled daily production build + Slack on failure
```

## Conventions

- **Model prefixes** — `stg_` (Silver staging), `fct_` (Gold fact), `dim_` (Gold dimension).
- **Multi-brand union** — every `stg_*` model uses `dbt_utils.union_relations(..., source_column_name='store_id')` across all brand Bronze sources. **Adding a new store:**
  1. Create `BRONZE_SHOPIFY_<NEW>` + `BRONZE_KLAVIYO_<NEW>` schemas.
  2. Add the matching Airbyte connections.
  3. Add both to `dbt/models/silver/_sources.yml`.
  4. Append to the `relations=[...]` list in every `stg_*` model that includes that source type.
  Gold and Lightdash require no changes.
- **`store_id` is the universal brand key** — present on every Silver+ table. Use it for joins and Lightdash dashboard filters (portfolio view = unfiltered; per-brand view = filtered).
- **Email normalisation** — `LOWER(TRIM(email))` in Silver before joining Shopify customers to Klaviyo profiles.
- **Currency** — Shopify returns a per-order `currency`. Normalisation strategy (query-time vs GBP in Silver) is undecided — preserve the `currency` column everywhere until a decision is made.
- **Testing** — `not_null` + `unique` on every primary key; range tests on revenue columns.
- **Incremental sync in Airbyte** is the default; full refresh only for small reference tables (products, campaigns).

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
| All of the above | 1Password (source of truth) |

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
