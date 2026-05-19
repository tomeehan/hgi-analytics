# 005: Cross-brand "April at a glance" table

> **Read this first if you are a Claude session opening this ticket cold.**
>
> **Project (one paragraph):** This repo is `hgi-analytics`. We ingest Shopify, Klaviyo, Meta, GA4, Google Ads, Cin7 and Prospect CRM into Snowflake via Airbyte, transform with dbt (Bronze, Silver, Gold), and serve dashboards from Lightdash. Full project README is `CLAUDE.md` in the repo root. Read it first if you have not seen this project before.
>
> **Wider goal of these tickets:** Recreate the **April 2026 KPI Report** PDF (`reference/april_2026_kpi_report.pdf`) as a live, brand and month filterable dashboard in Lightdash. The PDF is treated as numerically authoritative. Each ticket builds one tile on the **Group Overview** dashboard and verifies the April 2026 number against the PDF.
>
> **The generator that produced this ticket:** `tickets/_ticket_generator.md`. Read sections (c) data availability map and (d) filter design before starting if you have not touched these tickets before.
>
> **Context window discipline:** Spawn subagents (Explore for codebase searches, Plan for design questions, general purpose for multi step research) so this session's context stays focused on the implementation. Do not foreground read every file linked from this ticket. Delegate.
>
> **This ticket is fully autonomous.** You are responsible for taking the work from Triage all the way to merged, deployed, migration run, and verified via the Lightdash API. Do not stop for human approval at any intermediate step. The end state is: PR merged to main, deploy action green, migration script applied, dashboard tile value verified against the PDF by API call, Basecamp card moved to Done with a verification comment.

## End to end workflow (run this top to bottom, autonomously)

1. **Claim the card on Basecamp.** Using the `basecamp` skill, find this ticket on the Data Engineering card table (account `5735756`, bucket `46863097`, card table `9778948512`), and move it from **Triage** to **In progress**.
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-005-cross_brand_april_at_a_glance`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes: this ticket has the largest dbt footprint in the batch so far. Add a new Gold model `fct_brand_monthly_summary` (rationale in the "dbt work" section), extend `fct_ga_sessions` so it carries a `transactions` column, and declare the explore's metrics on the new model. Run `cd dbt && dbt build --select fct_brand_monthly_summary+` and confirm tests pass.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration cross_brand_april_at_a_glance`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-005-cross_brand_april_at_a_glance`.
   - `gh pr create` with a body that includes the **Post deploy ops** line verbatim (see template at the bottom of this ticket).
5. **Self merge on green CI.**
   - Wait around 10 seconds, then `gh pr checks <pr-number> --watch` until CI is green.
   - `gh pr merge --rebase --delete-branch`. Never push to main directly. Never use `--no-verify` or skip hooks.
6. **Watch the deploy.**
   - The `lightdash_deploy.yml` workflow fires automatically on push to main. Poll with `gh run list --workflow=lightdash_deploy.yml --limit 1 --json status,conclusion,databaseId --jq '.[0]'`, or `gh run watch <run-id>`. Wait until `status=completed, conclusion=success`.
7. **Run the migration.**
   - `python3 lightdash/migrations/<file>` (no `--dry-run` this time). The migration mutates Lightdash state via the API and should print one line per API call.
8. **Verify via the Lightdash API (not the browser).**
   - Import the helpers from `lightdash/migrations/_lib.py` (or curl with auth from `.env`) and:
     - `GET /api/v1/dashboards/a8941b36-5393-43fb-9714-cd7edb582803` to confirm the new tile UUIDs are present in `tiles[]`.
     - For each new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert the returned values equal the expected April numbers from this ticket (see the EXPECTED block in the verification snippet).
     - Repeat the API query with Month=March-2026 to capture the March values (needed for the Basecamp comment, and proves the month filter works end to end).
9. **Close the loop on Basecamp.**
   - Add a comment to the card with:
     - the merged PR URL,
     - the verified April and March totals (from step 8),
     - the dashboard tile UUIDs you just created (table tile + glossary markdown tile),
     - any caveats or known gaps (especially the iSC Shopify sync gap and the fact that GA4 is currently iSC-only, link the prerequisite tickets).
   - Move the card from **In progress** to **Done**.
10. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference

- File: `reference/april_2026_kpi_report.pdf`
- Page 2, full-width table titled **"April 2026 at a glance"** under the section header **"ACROSS ALL FOUR BRANDS"**.
- The table is the showpiece of page 2. Verbatim contents:

| BRAND | REVENUE (SHOPIFY*) | SHOPIFY ORDERS | SESSIONS | TRANS (GA) | SHOPIFY CVR | SHOPIFY RPS | VS MAR (GA) | VS APR 25 (GA) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Revitalash | £266,908 | 2,669 | 29,730 | 1,457 | 8.98%* | £8.98* | - | - |
| iS Clinical | £144,532 | 1,075 | 15,682 | 554 | 6.85%* | £9.21* | - | - |
| Deese PRO | £13,731 | 20 | 7,649 | 17 | 0.26% | £1.79 | - | - |
| Harpar Grace Intl | £3,157 | 27 | 2,167 | 18 | 1.25%* | £1.46* | - | - |
| **Total (Shopify SoT)** | **£428,328** | **3,791** | **55,228** | **2,046** | - | - | - | - |

Below the table the PDF prints a glossary:

> *Glossary:*
> *CVR* (Conversion Rate) = orders / sessions. The proportion of website visits that resulted in a purchase. Higher = better.
> *Shopify CVR* = Shopify orders / GA4 sessions. Higher than GA-only CVR because Shopify counts all orders including subscription auto-renewals, mobile app, and untracked sessions.
> *RPS* (Revenue Per Session) = revenue / sessions. The average revenue generated by each website visit. Higher = better.
> *Shopify RPS* = Shopify revenue / GA4 sessions.
> *AOV* (Average Order Value) = revenue / orders.
> *: Revenue is Shopify source of truth used everywhere it's available (all 4 brands this month).

- March 2026 values: not on the PDF page 2. Capture the totals row from the Lightdash API at verification time (step 8) and write into the Basecamp comment.

## Metric definition

A per-brand Lightdash **table tile** reproducing the 4-row by 9-column PDF table, plus a totals row. Each row is one brand; the rows are static (the table always lists Revitalash, iS Clinical, Deese PRO, Harpar Grace Intl, irrespective of the Brand filter, per the layout decision in generator section (d): "Brand filter does not switch the view, it only filters the data"). When a single brand is selected from the dashboard's Brand filter, only that row's data populates; the other rows still appear but show zeros / blanks.

Columns (Lightdash dimension or metric on the explore in brackets):

- **Brand** (dimension `store_id` from the new `fct_brand_monthly_summary` explore, rendered via the existing label/rename map "Brand" + display values).
- **Revenue (Shopify)** = `sum(shopify_revenue)` per `store_id` for the selected month. PDF April values: RL £266,908, ISC £144,532, Deese £13,731, HGI £3,157, total £428,328.
- **Shopify Orders** = `sum(shopify_orders)` per `store_id` for the selected month. PDF April: RL 2,669, ISC 1,075, Deese 20, HGI 27, total 3,791.
- **Sessions** = `sum(ga_sessions)` per `store_id`. PDF April: RL 29,730, ISC 15,682, Deese 7,649, HGI 2,167, total 55,228.
- **Trans (GA)** = `sum(ga_transactions)` per `store_id`. PDF April: RL 1,457, ISC 554, Deese 17, HGI 18, total 2,046.
- **Shopify CVR** = Shopify orders / GA sessions * 100. Declared as a Lightdash metric on the explore so it recomputes when filters change. PDF: 8.98% RL, 6.85% ISC, 0.26% Deese, 1.25% HGI.
- **Shopify RPS** = Shopify revenue / GA sessions. Declared as a Lightdash metric on the explore. PDF: £8.98 RL, £9.21 ISC, £1.79 Deese, £1.46 HGI.
- **vs Mar (GA)** = percent change in `ga_sessions` from the previous calendar month. PDF shows "-" for April 2026 because the comparison month (March) is not summarised on the PDF; surface as a Lightdash metric (period over period change), it will populate as the source data lands.
- **vs Apr 25 (GA)** = year-on-year delta on `ga_sessions`. PDF shows "-" today (no full year of GA history yet). Same treatment as "vs Mar".

Filter behaviour:

- **Month filter** changes which month populates the table.
- **Brand filter** = All shows all four brand rows populated. Brand = a specific store shows only that store's row populated; the other rows render with zeros (per generator section (d)).

## Data dependencies

### Bronze sources

- ok `BRONZE_SHOPIFY_REVITALASH.ORDERS`, 5,578 orders all-time, 2,637 in April 2026 (£263,317) versus PDF 2,669 / £266,908. Minor gap of around 32 orders / £3,591.
- blocked `BRONZE_SHOPIFY_ISCLINICAL.ORDERS`, only **175 orders all-time**, earliest 2026-02-26. April 2026 has 29 orders / £3,392 versus PDF's 1,075 / £144,532. Same data gap surfaced in tickets 001 and 002. **This ticket cannot reach the PDF's April totals row until the iSC Shopify sync is fixed.** Link the prerequisite sibling ticket: "Backfill / repair iSC Shopify Airbyte sync, only 175 orders since 2026-02-26".
- ok `BRONZE_SHOPIFY_DEESE_PRO.ORDERS`, 3,233 all-time, 20 in April 2026 / £13,731. Matches PDF exactly.
- blocked `BRONZE_SHOPIFY_GESKE.ORDERS`, no `ORDERS` table. Geske is not a row in the PDF page 2 table, so this is fine for this ticket.
- blocked `BRONZE_SHOPIFY_HARPER_GRACE`, harpargrace.com is not connected at all. The HGI row on the page 2 table is therefore blank today. Link the prerequisite sibling ticket: "Connect harpargrace.com Shopify to Airbyte".
- ok `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT`, 30 days of April 2026 loaded, 15,638 sessions in April (PDF: 15,682, gap of 44).
- blocked `BRONZE_GOOGLE_ANALYTICS_REVITALASH`, not declared as a source; GA4 is not connected for Revitalash. **Prerequisite ticket: "Connect Revitalash GA4 property to Airbyte"** (Sessions and Trans columns will show 0 for Revitalash until this lands).
- blocked `BRONZE_GOOGLE_ANALYTICS_DEESE_PRO`, not declared, not connected. **Prerequisite ticket: "Connect Deese PRO GA4 property to Airbyte"**.
- blocked `BRONZE_GOOGLE_ANALYTICS_HARPAR_GRACE_INTL`, not declared, not connected. **Prerequisite ticket: "Connect Harpar Grace Intl GA4 property to Airbyte"** (matching the missing harpargrace.com Shopify connection).

Net: Sessions and Trans columns populate **for iS Clinical only today**. The other three brands will show 0 sessions / 0 trans, which makes the per-row Shopify CVR and Shopify RPS divide by zero (null). The migration should render those as `-` to match the PDF formatting when the denominator is null.

### GA4 "transactions" column

The PDF's "Trans (GA)" column is the count of `purchase` events in GA4. The current `stg_google_analytics__sessions` model derives only `sessions`, `engaged_sessions`, and `total_revenue` from `traffic_acquisition_session_source_medium_report`, which does **not** carry an event count. Options to produce a daily transactions count by `store_id`:

1. Add a CTE that reads `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.CONVERSIONS_REPORT` filtered to `eventname = 'purchase'`, summed by `date`, and left-joined into the sessions rollup on (`session_date`, `store_id`). The `CONVERSIONS_REPORT` row count for `purchase` should be the per-day purchase event count.
2. Alternatively, derive transactions from `ECOMMERCE_PURCHASES_ITEM_ID_REPORT` by summing `ITEMSPURCHASED` and dividing by an items-per-order assumption, but this is a worse signal: prefer option 1.

Pick option 1. Document the choice in the model's docstring.

### Silver / Gold models

- ok `dbt/models/silver/stg_shopify__orders.sql`, multi-brand union by `store_id`.
- ok `dbt/models/silver/stg_google_analytics__sessions.sql`, currently iSC only. **Extend** to add a `transactions` column (option 1 above) and to fan out across the other brands' bronze schemas if those connections land before this ticket ships (in which case add the matching `bronze_google_analytics_<brand>` sources to `_sources.yml`).
- ok `dbt/models/gold/fct_orders.sql`, the Shopify side of the join.
- ok `dbt/models/gold/fct_ga_sessions.sql`, the GA side of the join. **Extend** the `_schema.yml` entry to declare a `transactions` column and a `total_ga_transactions` metric.
- new `dbt/models/gold/fct_brand_monthly_summary.sql`, see "dbt work" below.

## dbt work

The decision between (a) a new Gold model `fct_brand_monthly_summary` and (b) declaring `joins:` on `fct_orders`'s schema yml: **go with (a), the new Gold model**. Reasoning:

- The table needs a `(store_id, order_month)` grain row for **every** brand, populated even when the brand has no Shopify or no GA data (the PDF table always lists Revitalash / iS Clinical / Deese PRO / Harpar Grace Intl). A `joins:` declaration would inner-join `fct_orders` to `fct_ga_sessions` and drop rows where one side is empty, which is exactly the wrong behaviour. A bespoke Gold model can full-outer-join the two facts and use a `brand_axis` CTE to guarantee one row per brand-month.
- Two derived metrics (Shopify CVR and Shopify RPS) need a divisor (sessions) that comes from the GA side, and a numerator (orders / revenue) from the Shopify side. Declaring those as Lightdash metrics on a single underlying table is cleaner than declaring them on a joined explore, which would require `${fct_ga_sessions.sessions}` style cross-model references and complicates the dry-run.
- Materialising a small per-brand-per-month summary is cheap and serves the entire page 2 of the PDF (this table + the two share-by-brand callouts in tickets 006 and 007 can read from the same summary).

### New model: `dbt/models/gold/fct_brand_monthly_summary.sql`

Columns:

- `store_id` (text, not null)
- `order_month` (date, not null, first day of month)
- `shopify_revenue` (numeric, sum of `fct_orders.total_price` for the brand-month)
- `shopify_orders` (numeric, count of `fct_orders.order_id` for the brand-month)
- `ga_sessions` (numeric, sum of `fct_ga_sessions.sessions`)
- `ga_transactions` (numeric, sum of `fct_ga_sessions.transactions` once added)
- `ga_total_revenue` (numeric, sum of `fct_ga_sessions.total_revenue`, included so it can power tickets 006 / 008)

Construction pattern:

```sql
with brand_axis as (
    -- One row per (store_id, order_month) the dashboard might filter on.
    -- Include all brands the PDF mentions, even if they have no data today.
    select store_id, order_month
    from {{ ref('fct_orders') }}
    union
    select store_id, date_trunc('month', session_date)::date as order_month
    from {{ ref('fct_ga_sessions') }}
    -- Optionally add a static brand list so HGI and Geske appear once
    -- harpargrace.com / GA4 connections land. Decide in implementation.
),

shopify as (
    select store_id, order_month,
           sum(total_price) as shopify_revenue,
           count(distinct order_id) as shopify_orders
    from {{ ref('fct_orders') }}
    group by 1, 2
),

ga as (
    select store_id,
           date_trunc('month', session_date)::date as order_month,
           sum(sessions) as ga_sessions,
           sum(transactions) as ga_transactions,
           sum(total_revenue) as ga_total_revenue
    from {{ ref('fct_ga_sessions') }}
    group by 1, 2
)

select
    a.store_id,
    a.order_month,
    coalesce(s.shopify_revenue, 0) as shopify_revenue,
    coalesce(s.shopify_orders, 0)  as shopify_orders,
    coalesce(g.ga_sessions, 0)     as ga_sessions,
    coalesce(g.ga_transactions, 0) as ga_transactions,
    coalesce(g.ga_total_revenue, 0) as ga_total_revenue
from brand_axis a
left join shopify s using (store_id, order_month)
left join ga      g using (store_id, order_month)
```

Materialise as a `table` (small, dashboard reads).

### Schema yml additions

Append a new `models:` entry for `fct_brand_monthly_summary` to `dbt/models/gold/_schema.yml`:

- `store_id` dimension with `label: Brand` and the same value-rename `case` expression used on `fct_orders` (paste verbatim from ticket 001's edit).
- `order_month` dimension with `label: Month`.
- Metrics: `shopify_revenue_total`, `shopify_orders_total`, `ga_sessions_total`, `ga_transactions_total`, `ga_revenue_total` (`sum` of the respective columns, format gbp where applicable, round 0).
- Derived metrics (Lightdash `type: number` with a `sql:` expression so they recompute on filters):
  - `shopify_cvr` = `sum(${TABLE}.shopify_orders)::float / nullif(sum(${TABLE}.ga_sessions), 0)`, format percent, round 2.
  - `shopify_rps` = `sum(${TABLE}.shopify_revenue)::float / nullif(sum(${TABLE}.ga_sessions), 0)`, format gbp, round 2.
  - `vs_mar_ga_sessions` and `vs_apr_25_ga_sessions`: stub these out with a TODO comment in the schema yml; the period-over-period and year-on-year deltas need either Lightdash table calculations on the tile or a window function in the model. Decide in implementation; the PDF shows `-` for both columns today so they are non-blocking.

Also extend `fct_ga_sessions`'s schema yml entry: add the new `transactions` column (description: "GA4 purchase event count, derived from `CONVERSIONS_REPORT` filtered to `eventname = 'purchase'`") and a `total_ga_transactions` metric (sum, round 0).

### Tests

On `fct_brand_monthly_summary`:

- `not_null` on `store_id` and `order_month`.
- `dbt_utils.unique_combination_of_columns` on `[store_id, order_month]`.
- Range tests on numeric outputs (`accepted_range` with `min_value: 0` on `shopify_revenue`, `shopify_orders`, `ga_sessions`, `ga_transactions`, `ga_total_revenue`) to catch negative-spend / negative-orders bugs.

## Lightdash work

This ticket creates **two tiles** under the cover KPIs (which are tickets 001 to 004), on what is conceptually page 2 of the dashboard.

1. **A large table tile** labelled **"April 2026 at a glance"** (the title updates dynamically when a different month is selected via the filter, since the page header reads "across all four brands"). Underlying explore: `fct_brand_monthly_summary`. Rows: dimension `store_id`. Columns (in this order, matching the PDF):
   - Revenue (Shopify) -> `shopify_revenue_total`, GBP format.
   - Shopify Orders -> `shopify_orders_total`, integer.
   - Sessions -> `ga_sessions_total`, integer.
   - Trans (GA) -> `ga_transactions_total`, integer.
   - Shopify CVR -> `shopify_cvr`, percent.
   - Shopify RPS -> `shopify_rps`, GBP.
   - vs Mar (GA) -> placeholder, render as `-` until the period-over-period metric is implemented.
   - vs Apr 25 (GA) -> placeholder, render as `-`.
   The table must respect the Brand + Month dashboard filters (verify by toggling). It must also expose `store_id` and `order_month` on the underlying explore so the filters land cleanly, per generator section (d) "Tile compliance".

2. **A markdown sub-tile directly underneath** the table, labelled **"Glossary"**. Content (verbatim from the PDF):

   > **CVR** (Conversion Rate) = orders / sessions. The proportion of website visits that resulted in a purchase. Higher = better.
   > **Shopify CVR** = Shopify orders / GA4 sessions. Higher than GA-only CVR because Shopify counts all orders including subscription auto-renewals, mobile app, and untracked sessions.
   > **RPS** (Revenue Per Session) = revenue / sessions. The average revenue generated by each website visit. Higher = better.
   > **Shopify RPS** = Shopify revenue / GA4 sessions.
   > **AOV** (Average Order Value) = revenue / orders.
   > *: Revenue is Shopify source of truth used everywhere it's available.

Migration filename: produced by `bin/new-lightdash-migration cross_brand_april_at_a_glance` (yields `lightdash/migrations/YYYYMMDD_HHMMSS_cross_brand_april_at_a_glance.py`). The migration must:

- Create the new table chart on `fct_brand_monthly_summary` with the seven displayable columns (vs Mar / vs Apr 25 are no-op placeholders, document as a follow-up in the migration's docstring).
- Create the markdown glossary tile.
- Attach both tiles to dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`, positioned on the "page 2" row of the dashboard (read the existing dashboard's `tiles[]` to find the boundary between page 1 and page 2, then append underneath).
- Be idempotent so re-running the script does not duplicate the tiles (check by chart name / tile UUID before POSTing).
- Support `--dry-run`.

## API verification snippet

Run this from the repo root after step 7 of the workflow. EXPECTED values are the PDF totals row; actual values today will not match because of the data gaps documented above (Shopify short ~ £145k from the iSC sync gap and ~ £3k from missing HGI; GA4 sessions / trans will only have iS Clinical data populated). The asserts are intentionally permissive: log expected vs actual and surface the gap in the Basecamp comment, do not block the workflow.

```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"

# PDF totals row, page 2 "April 2026 at a glance".
EXPECTED_APRIL = {
    "shopify_revenue_total":  428328,
    "shopify_orders_total":   3791,
    "ga_sessions_total":      55228,
    "ga_transactions_total":  2046,
}

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace `<table-chart-uuid>` with the UUID printed by the migration.
results = api("POST", "/saved/<table-chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_brand_monthly_summary_order_month"},
         "operator": "equals", "values": ["2026-04-01"]},
    ]},
})

# The response has one row per `store_id`. Sum the metric columns across rows
# to get the totals-row equivalent.
totals = {k: 0 for k in EXPECTED_APRIL}
for row in results["rows"]:
    for k in EXPECTED_APRIL:
        cell = row.get(f"fct_brand_monthly_summary_{k}")
        if cell:
            totals[k] += cell["value"]["raw"] or 0

print("April totals (today):", totals)
print("PDF expected:         ", EXPECTED_APRIL)
for k, expected in EXPECTED_APRIL.items():
    if totals[k] != expected:
        print(f"  MISMATCH {k}: got {totals[k]}, PDF {expected}. Surface in Basecamp comment.")

# Repeat for March 2026 to confirm the Month filter wires through. Capture the
# totals row into the Basecamp comment.
march = api("POST", "/saved/<table-chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_brand_monthly_summary_order_month"},
         "operator": "equals", "values": ["2026-03-01"]},
    ]},
})
march_totals = {k: 0 for k in EXPECTED_APRIL}
for row in march["rows"]:
    for k in EXPECTED_APRIL:
        cell = row.get(f"fct_brand_monthly_summary_{k}")
        if cell:
            march_totals[k] += cell["value"]["raw"] or 0
print("March totals:", march_totals)
```

If the response field id differs from `fct_brand_monthly_summary_<metric>`, inspect `results["rows"][0]` once and adjust. If the chart does not exist yet at API call time, fall back to `POST /api/v1/projects/<projectUuid>/explores/fct_brand_monthly_summary/runQuery` with the same dimensions / metrics.

## Snowflake fallback SQL

If the API path fails or the answer disagrees with the PDF in a way you cannot explain, reproduce the table directly from Snowflake via `snow sql -c hgi`:

```sql
-- Per-brand "April 2026 at a glance" (today's data)
with shopify as (
    select store_id,
           sum(total_price)            as shopify_revenue,
           count(distinct order_id)    as shopify_orders
    from HGI.GOLD.FCT_ORDERS
    where order_month = '2026-04-01'
    group by 1
),

ga as (
    select store_id,
           sum(sessions)               as ga_sessions,
           -- transactions column added by this ticket; until then derive inline:
           (select count(*) from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.CONVERSIONS_REPORT
            where eventname = 'purchase' and date between '20260401' and '20260430') as ga_transactions
    from HGI.GOLD.FCT_GA_SESSIONS
    where session_date >= '2026-04-01' and session_date < '2026-05-01'
    group by 1
),

brand_axis as (
    select 'revitalash'  as store_id union all
    select 'isclinical'           union all
    select 'deese_pro'            union all
    select 'geske'                union all
    select 'harpar_grace_intl'
)

select
    a.store_id,
    coalesce(s.shopify_revenue, 0) as shopify_revenue,
    coalesce(s.shopify_orders, 0)  as shopify_orders,
    coalesce(g.ga_sessions, 0)     as ga_sessions,
    coalesce(g.ga_transactions, 0) as ga_transactions,
    case when coalesce(g.ga_sessions, 0) > 0
         then coalesce(s.shopify_orders, 0)::float / g.ga_sessions * 100
         else null end as shopify_cvr_pct,
    case when coalesce(g.ga_sessions, 0) > 0
         then coalesce(s.shopify_revenue, 0)::float / g.ga_sessions
         else null end as shopify_rps
from brand_axis a
left join shopify s using (store_id)
left join ga      g using (store_id)
order by shopify_revenue desc nulls last;

-- Totals row
select
    sum(total_price)         as shopify_revenue_total,
    count(distinct order_id) as shopify_orders_total
from HGI.GOLD.FCT_ORDERS
where order_month = '2026-04-01';

select sum(sessions) as ga_sessions_total
from HGI.GOLD.FCT_GA_SESSIONS
where session_date >= '2026-04-01' and session_date < '2026-05-01';

select count(*) as ga_transactions_total
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.CONVERSIONS_REPORT
where eventname = 'purchase' and date between '20260401' and '20260430';

-- March 2026 (for filter-change validation, capture into the Basecamp comment)
select store_id,
       sum(total_price) as rev,
       count(distinct order_id) as orders
from HGI.GOLD.FCT_ORDERS
where order_month = '2026-03-01'
group by 1
order by 1;
```

Expected April totals today (loaded data only): Shopify revenue around £279,895, Shopify orders around 2,686, GA sessions around 15,638 (iSC only), GA transactions = the iSC purchase-event count (verify on the day). PDF target: Shopify £428,328 / 3,791 orders / 55,228 sessions / 2,046 trans.

## Post deploy ops (paste into the PR description)

> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_cross_brand_april_at_a_glance.py` (step 7).

(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed

This ticket introduces a new Gold model (`fct_brand_monthly_summary`) and extends `fct_ga_sessions` with a `transactions` column. Update `CLAUDE.md` in the same PR:

- Under "High-level architecture" -> "Gold", add `fct_brand_monthly_summary` to the bullet list with a one-line description ("per-brand-per-month cross-source summary, Shopify + GA4, powers the page-2 'at a glance' table and the share-by-brand callouts").
- Under "Conventions", document the brand-axis pattern: cross-source summary models should `union` the source store_ids onto a static brand list so brands appear with zeros even when one source is missing, mirroring the PDF layout decision in generator section (d).
- If GA4 connections for Revitalash / Deese PRO / HGI land while this ticket is in flight, update the GA4 section of `CLAUDE.md` accordingly.
