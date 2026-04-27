# Lightdash

Lightdash is self-hosted on **Hetzner Cloud** (`hgi-lightdash`, type `cpx22` in
`fsn1`). Caddy fronts it with auto Let's Encrypt TLS at
[`lightdash.hgi.tomeehan.net`](https://lightdash.hgi.tomeehan.net).

It reads metric definitions from this repo's `dbt/` project and queries
Snowflake Gold/Silver/Metrics via the `lightdash_user` (role `REPORTER`).

## Architecture

```
Browser ──▶ Cloudflare DNS ──▶ Hetzner cpx22 (fsn1)
                                ├── Caddy (TLS termination, port 80/443)
                                └── lightdash/lightdash:latest (port 8080)
                                       │
                                       ├── Neon Postgres (metadata, eu-west-2)
                                       └── Snowflake (warehouse data, eu-west-2)
```

- **App state** (users, dashboards, saved queries) → Neon (free tier, project
  `Lightdash`, region `aws-eu-west-2`). Backups + PITR handled by Neon.
- **Warehouse data** → Snowflake `HGI` database, schema `GOLD`.
- **The Hetzner server is stateless** — rebuilding it from `cloud-init`
  recreates a working Lightdash pointed at the same Neon DB.

## Server config

Live config lives on the server at `/opt/lightdash/`:

- `docker-compose.yml` — the lightdash + caddy stack
- `Caddyfile` — TLS + reverse proxy to `lightdash:8080`
- `.env` — `PGCONNECTIONURI` (Neon) and `LIGHTDASH_SECRET` (`chmod 600`)

To redeploy after a Lightdash version bump:

```sh
ssh root@lightdash.hgi.tomeehan.net
cd /opt/lightdash
docker compose pull && docker compose up -d
```

## Secrets

| Secret | Stored in |
|---|---|
| `LIGHTDASH_SECRET` (random 32-byte hex) | `/opt/lightdash/.env` on the server |
| `PGCONNECTIONURI` (Neon metadata DB) | `/opt/lightdash/.env` on the server |
| Snowflake `lightdash_user` password | Lightdash UI → Connections (stored encrypted in Neon) |

## Project connection

- **dbt project**: deployed via the [Lightdash CLI](https://docs.lightdash.com/guides/cli/intro)
  (`lightdash deploy` from inside `dbt/`). The hardening ticket covers wiring
  this up as a GitHub Action so production stays in sync with `main`.
- **Warehouse**: Snowflake — user `lightdash_user`, role `REPORTER`,
  warehouse `HGI_WH`, database `HGI`, schema `GOLD`.

## Metrics

Metrics are defined in dbt YAML (`dbt/models/gold/_schema.yml`) under
`meta.metrics` — never duplicated in Lightdash. Lightdash discovers them on
sync.

## Building dashboards locally

The two `build_*.py` scripts in this directory create dashboards via the
Lightdash REST API. They read auth from `.env` (see `.env.example`) — populate
`LIGHTDASH_URL`, `LIGHTDASH_TOKEN`, `LIGHTDASH_PROJECT_UUID`, `LIGHTDASH_SPACE_UUID`,
then run `python3 lightdash/build_prospect_crm_dashboards.py` (or
`build_dashboards.py`). Note: the scripts POST new dashboards on every run —
they don't upsert. Delete stale ones via the UI before re-running.

## Hardening

See [Basecamp card 9784511568](https://3.basecamp.com/5735756/buckets/46863097/card_tables/cards/9784511568)
for the deferred hardening backlog (rotate placeholder passwords, Cloudflare
proxy, SSH lockdown, automated deploys, monitoring, committing the docker
compose config to this repo).
