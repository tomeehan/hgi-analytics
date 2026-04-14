# Lightdash

Lightdash is self-hosted on Fly.io (`hgi-lightdash`, region `lhr`). It reads
metric definitions directly from this repo's `dbt/` project and queries
Snowflake Gold/Silver/Metrics via the `lightdash_user` (role `REPORTER`).

## Deployment

The Fly app config lives in `fly.toml` (to be added). Deploy with:

```sh
fly deploy --config lightdash/fly.toml
```

Required Fly secrets:
- `LIGHTDASH_SECRET` — random 32-byte hex (generate via `openssl rand -hex 32`)
- Snowflake `REPORTER` password

Required persistent volume:
- `lightdash_data` (5 GB, region `lhr`)

## Project connection

- dbt repo: GitHub → point at `dbt/` subdirectory (requires a GitHub PAT)
- Warehouse: Snowflake
  - User: `lightdash_user` · Role: `REPORTER`
  - Database: `HGI` · Warehouse: `HGI_WH`

## Metrics

Metrics are defined in dbt YAML (`dbt/models/gold/_schema.yml`) under `meta.metrics`
— never duplicated in Lightdash. Lightdash discovers them on sync.
