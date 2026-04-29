# Lightdash migrations

One-shot scripts that mutate live Lightdash state (saved charts,
dashboards) after a PR has been merged and `lightdash_deploy.yml` has
refreshed dbt metadata.

## Why this exists

`lightdash deploy` only refreshes the dbt project — it does **not**
update saved-chart configs (column order, dimensions, eCharts
formatters), recreate dashboards, or delete obsolete ones. The legacy
`lightdash/build_dashboards.py` and `build_prospect_crm_dashboards.py`
scripts are kept for **historical reference only** — they were
one-shots used to seed the initial dashboards and must not be re-run
(they POST new charts on every invocation, so re-running creates
duplicates).

For everything else — chart edits, dimension changes, dashboard
deletions, formatter swaps — write a timestamped migration here.

## Conventions

- One file per merged PR's dashboard ops. Filename:
  `YYYYMMDD_HHMMSS_<short_slug>.py`.
- Each migration's docstring states the originating PR, what it
  changes, what state it expects, and a `Status:` line that's flipped
  from `pending` to `applied YYYY-MM-DD` once it's run.
- Migrations are run-once. They should not be idempotent at the
  expense of clarity — the audit trail is the point.
- Scaffold a new one with `bin/new-lightdash-migration <slug>`.

## Running a migration

```sh
# 1. Wait for lightdash_deploy.yml to finish on main
gh run watch $(gh run list --workflow lightdash_deploy.yml --limit 1 --json databaseId -q '.[0].databaseId')

# 2. Run the migration
python3 lightdash/migrations/<timestamp>_<slug>.py

# 3. Edit the migration's docstring and flip Status to "applied <date>"
# 4. Commit the docstring change
```

## Library

`_lib.py` exposes `api(method, path, body=None, allow_404=False)` plus
the four `LIGHTDASH_*` env-derived identifiers. Migrations import from
it via a local `sys.path` insert — see `_template.py`.
