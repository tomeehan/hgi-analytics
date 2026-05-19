# 006: GA4 revenue share by brand

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-006-ga4-revenue-share-by-brand`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes: add `order_month` to `stg_google_analytics__sessions` (and the matching `_schema.yml` entries on Silver and Gold) so the dashboard Month filter targets a stable field. Then run `cd dbt && dbt build --select fct_ga_sessions+` and confirm tests pass.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration ga4_revenue_share_by_brand`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-006-ga4-revenue-share-by-brand`.
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
     - `GET /api/v1/dashboards/a8941b36-5393-43fb-9714-cd7edb582803` to confirm the new tile UUID is present in `tiles[]`.
     - For the new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert each brand's share rounds to the expected April number listed in the verification snippet below.
     - Repeat the API query with Month=March-2026 to capture the March values (needed for the Basecamp comment, and proves the month filter works end to end).
9. **Close the loop on Basecamp.**
   - Add a comment to the card with:
     - the merged PR URL,
     - the verified April and March values per brand (from step 8),
     - the dashboard tile UUID you just created,
     - any caveats or known gaps. Today's tile will show 100% iS Clinical because GA4 is only connected for iSC. Call this out explicitly and link the three Airbyte connection prerequisite tickets (see "Data dependencies").
   - Move the card from **In progress** to **Done**.
10. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page 2, bottom left sub box, label "GA4 REVENUE SHARE BY BRAND".
- April 2026 values (PDF):
  - Revitalash **62.7%**
  - iS Clinical **32.3%**
  - Deese PRO **4.0%**
  - Harpar Grace **0.9%**
- Cross check from the per brand "Revenue & Channel Attribution" pages: GA-attributed revenue per brand for April is RL £143,188, iSC £73,808, Deese £9,194, HGI £2,011, summing to £228,201. 143188 / 228201 = 62.75% (PDF rounds to 62.7); 73808 / 228201 = 32.34%; 9194 / 228201 = 4.03%; 2011 / 228201 = 0.88%. Numbers reconcile.
- March 2026 values: not on the PDF. Capture from the Lightdash API at verification time and write into the Basecamp comment.

## Metric definition

Percentage of total GA4-attributed revenue contributed by each brand, for the selected month. Computed as:

```
brand_share = (brand_ga_revenue / sum(brand_ga_revenue across all loaded brands in the month)) * 100
```

- Source of truth: GA4 via Airbyte, landing in `BRONZE_GOOGLE_ANALYTICS_<BRAND>.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT`. The `totalrevenue` column on that report is the GA "purchase" event revenue, exposed in Silver as `total_revenue`.
- The PDF appendix on page 31 names GA4 as the channel attribution source of truth (Shopify is used for "true" orders/revenue), so the share calculation must use GA-attributed revenue, **not** Shopify `total_price`. Do not substitute Shopify revenue into this tile.
- Currency: GBP. All loaded GA4 properties report in GBP.
- Filter behaviour:
  - **Month filter** changes which month's GA revenue is used for both numerator and denominator.
  - **Brand filter** = All renders one bar per brand. Selecting a single brand makes that brand's bar trivially 100% and the others 0%, which is acceptable per the "filter zeros, does not hide" layout decision in generator section (d). The tile is most useful with Brand = All; that's the default the dashboard ships with.

## Data dependencies

### Bronze sources
- Live `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT` (already a declared dbt source; data fresh to 2026-05-05 per the data availability map).
- Blocked `BRONZE_GOOGLE_ANALYTICS_REVITALASH` (not connected, not declared).
- Blocked `BRONZE_GOOGLE_ANALYTICS_DEESE_PRO` (not connected, not declared).
- Blocked `BRONZE_GOOGLE_ANALYTICS_HARPAR_GRACE` (not connected, not declared).

### Silver / Gold models
- `dbt/models/silver/stg_google_analytics__sessions.sql` exists and only reads from `bronze_google_analytics_isclinical`. The CTE pattern is set up to extend per brand (`isclinical as (...), unioned as (select * from isclinical)`), mirroring the multi brand union convention from `CLAUDE.md`.
- `dbt/models/gold/fct_ga_sessions.sql` is a thin pass through (`select * from {{ ref('stg_google_analytics__sessions') }}`). No structural change needed in the Gold file itself.
- `dbt/models/gold/_schema.yml` already declares `fct_ga_sessions` with `store_id`, `sessions`, `engaged_sessions`, `total_revenue`. **Missing:** `order_month`. This ticket adds it on the Silver staging.

### New columns required
- `order_month` (date, first day of the month) on `stg_google_analytics__sessions` and therefore on `fct_ga_sessions`. Computed as `date_trunc('month', session_date)`.

### Cross ticket dependencies (prerequisites, out of scope for this ticket)
Three prerequisite Airbyte connection tickets are needed before this tile will match the PDF. They are out of scope for this ticket; this ticket only builds the tile, ready for when the data arrives.

- **"Connect Revitalash GA4 to Airbyte"** (loads `BRONZE_GOOGLE_ANALYTICS_REVITALASH`).
- **"Connect Deese PRO GA4 to Airbyte"** (loads `BRONZE_GOOGLE_ANALYTICS_DEESE_PRO`).
- **"Connect Harpar Grace Intl GA4 to Airbyte"** (loads `BRONZE_GOOGLE_ANALYTICS_HARPAR_GRACE`).

When each lands, extend `stg_google_analytics__sessions` with a new per brand CTE (matching the existing `isclinical` block) and add it to the `unioned` CTE. No Gold or Lightdash changes will be needed; the tile will start showing the new brand automatically.

Until those prerequisites land, **this tile will show 100% iS Clinical** (the only loaded brand), which is misleading vs the PDF. The Basecamp verification comment for this ticket must call that out explicitly and link the three prerequisite tickets.

## dbt work

1. **Extend `dbt/models/silver/stg_google_analytics__sessions.sql`** to add `order_month`:

   ```sql
   with isclinical as (
       select
           to_date(date, 'YYYYMMDD') as session_date,
           date_trunc('month', to_date(date, 'YYYYMMDD')) as order_month,
           'isclinical' as store_id,
           sum(sessions) as sessions,
           sum(engagedsessions) as engaged_sessions,
           sum(totalrevenue) as total_revenue
       from {{ source('bronze_google_analytics_isclinical',
                      'traffic_acquisition_session_source_medium_report') }}
       where date is not null
       group by 1, 2, 3
   ),

   unioned as (
       select * from isclinical
   )

   select * from unioned
   ```

   When the Revitalash / Deese / HGI GA4 connections land, each adds a parallel CTE and an extra `union all` line in `unioned`. Do not refactor pre-emptively, just leave the shape ready.

2. **Update `dbt/models/silver/_schema.yml`** for `stg_google_analytics__sessions`:
   - Add `order_month` column with description "First day of the month the session occurred (date_trunc month of session_date)".
   - Keep the existing `not_null` tests on `session_date` and `store_id`.

3. **Update `dbt/models/gold/_schema.yml`** for `fct_ga_sessions`:
   - Add `order_month` column entry (same description).
   - Add the `store_id` value rename map (matching ticket 001's convention for `fct_orders`):
     ```yaml
     meta:
       dimension:
         label: "Brand"
         sql: "case ${TABLE}.store_id when 'revitalash' then 'Revitalash' when 'isclinical' then 'iS Clinical' when 'deese_pro' then 'Deese PRO' when 'geske' then 'Geske' else ${TABLE}.store_id end"
     ```
   - Confirm `total_revenue` already has a `sum` metric exposed (it does, per the existing `_schema.yml`). If not, add `total_ga_revenue` with `type: sum`, `label: "GA-attributed Revenue"`, `format: gbp`, `round: 0`.

4. **Build and test:**
   ```bash
   cd dbt && dbt deps && dbt build --select fct_ga_sessions+
   ```
   Expected: `fct_ga_sessions` rows for April 2026 carry `order_month = 2026-04-01`. `sum(total_revenue) where order_month = '2026-04-01' and store_id = 'isclinical'` should land near the PDF's £73,808 (small drift acceptable; GA4 numbers settle for several days after month end).

## Lightdash work

A single **horizontal bar chart** tile on the **Group Overview** dashboard, sitting in the cross brand summary row, mirroring the PDF page 2 layout (next to the "Meta spend share by brand" tile from ticket 007).

- **Tile type:** horizontal bar chart. Per the user's project memory preference for horizontal bars in Lightdash, set `flipAxes=true` on the chart config. Do not use a donut/pie despite the inventory description.
- **Label:** "GA4 revenue share by brand".
- **Underlying explore:** `fct_ga_sessions`.
- **X axis (post flip):** brand (dimension `store_id`, displayed via the Brand label/rename map).
- **Y axis (post flip):** percent-of-total of `total_revenue` for the filtered month. Implemented as a Lightdash **table calculation** that divides the brand row's `sum(total_revenue)` by the window total across all rows, multiplied by 100. Sketch:
  ```
  brand_share_pct = ${fct_ga_sessions.total_revenue} / SUM(${fct_ga_sessions.total_revenue}) OVER () * 100
  ```
  Format as percent with 1 dp so the displayed values match the PDF (e.g. 62.7%). Sort descending by share.
- **Filter wiring:** the dashboard level **Brand** and **Month** filters from ticket 001 auto apply, because `fct_ga_sessions` now exposes `store_id` (with the same Brand label/rename map as `fct_orders`) and `order_month`. Confirm by reading the dbt manifest after building, then by toggling the filter in the live dashboard after deploying.
- **Note on the Brand filter:** selecting a single brand makes the chart trivially 100% for that brand and 0% for the others. This is the intended behaviour per the layout decision in generator section (d) ("filter zeros, does not hide"). The Lightdash tile config does **not** need any special handling for this; the table calculation naturally returns 100% when one row is filtered in.

Migration filename: produced by `bin/new-lightdash-migration ga4_revenue_share_by_brand` (yields `lightdash/migrations/YYYYMMDD_HHMMSS_ga4_revenue_share_by_brand.py`). The migration must:
- Create the saved chart targeting `fct_ga_sessions` with the brand dimension, `sum(total_revenue)` metric, and the `brand_share_pct` table calculation. Set `chartConfig.config.flipAxes = true`.
- Attach the new tile to dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`, positioned alongside the ticket 007 Meta share tile per the PDF page 2 layout.
- Be idempotent / re-runnable safe per `lightdash/migrations/README.md`. Support `--dry-run`.
- Print the new chart UUID and tile UUID so they can be slotted into the verification snippet.

## API verification snippet

Run this in step 8 of the workflow above. The exact field IDs come from Lightdash's auto generated identifiers; check the explore via `GET /api/v1/projects/<project-uuid>/explores/fct_ga_sessions` if the names below don't match.

```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"

# PDF April 2026 expected shares (percent). One row per brand.
EXPECTED_APRIL = {
    "Revitalash":   62.7,
    "iS Clinical":  32.3,
    "Deese PRO":     4.0,
    "Harpar Grace":  0.9,
}

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace <chart-uuid> after the migration prints it
results = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_ga_sessions_order_month"}, "operator": "equals", "values": ["2026-04-01"]},
    ]},
})

# Build {brand: share} from the response
got = {}
for row in results["rows"]:
    brand = row["fct_ga_sessions_store_id"]["value"]["formatted"]
    share = round(row["brand_share_pct"]["value"]["raw"], 1)
    got[brand] = share
print("April shares (live):", got)

# Today's reality check: only iS Clinical is connected, so the live response
# will be {"iS Clinical": 100.0}. Once the three prerequisite Airbyte
# connections land, this assert should hold against the PDF.
if set(got.keys()) == {"iS Clinical"}:
    print("Expected stub: GA4 only connected for iSC; tile will show 100% iSC.")
    print("Link prerequisite tickets in the Basecamp comment.")
else:
    for brand, expected in EXPECTED_APRIL.items():
        assert abs(got.get(brand, 0) - expected) < 0.5, (
            f"April mismatch for {brand}: got {got.get(brand)}, expected {expected}"
        )
    print("April OK against PDF.")

# March, for the Basecamp comment + filter change validation
results_mar = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_ga_sessions_order_month"}, "operator": "equals", "values": ["2026-03-01"]},
    ]},
})
got_mar = {
    row["fct_ga_sessions_store_id"]["value"]["formatted"]:
        round(row["brand_share_pct"]["value"]["raw"], 1)
    for row in results_mar["rows"]
}
print("March shares (live):", got_mar)
```

If the saved chart doesn't exist yet (early in the migration), use `POST /api/v1/projects/<projectUuid>/explores/fct_ga_sessions/runQuery` against the explore directly with the same filter shape.

## Snowflake fallback SQL

If the API path fails or the answer disagrees with the PDF, reproduce the per brand share directly from Snowflake (`snow sql -c hgi`):

```sql
-- April 2026: GA revenue and share by brand
with monthly as (
    select
        store_id,
        sum(total_revenue) as ga_revenue
    from HGI.GOLD.FCT_GA_SESSIONS
    where order_month = '2026-04-01'
    group by 1
),
totals as (
    select sum(ga_revenue) as total_ga_revenue from monthly
)
select
    monthly.store_id,
    monthly.ga_revenue,
    round(monthly.ga_revenue / totals.total_ga_revenue * 100, 1) as brand_share_pct
from monthly cross join totals
order by brand_share_pct desc;

-- March 2026 (for filter change validation)
with monthly as (
    select store_id, sum(total_revenue) as ga_revenue
    from HGI.GOLD.FCT_GA_SESSIONS
    where order_month = '2026-03-01'
    group by 1
),
totals as (select sum(ga_revenue) as total_ga_revenue from monthly)
select
    monthly.store_id,
    monthly.ga_revenue,
    round(monthly.ga_revenue / totals.total_ga_revenue * 100, 1) as brand_share_pct
from monthly cross join totals
order by brand_share_pct desc;
```

Today both queries return a single row (`isclinical`, 100%) because only iS Clinical GA4 is loaded. Expected April breakdown per PDF page 2, once all four brands are loaded: Revitalash 62.7%, iS Clinical 32.3%, Deese PRO 4.0%, Harpar Grace 0.9%.

## Post deploy ops (paste into the PR description)
> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_ga4_revenue_share_by_brand.py` (step 7).

(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed

This ticket does not introduce a new source, role, or convention. `CLAUDE.md` already lists `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` as the only GA4 schema. If, at the time this ticket is implemented, one or more of the three prerequisite GA4 connections have already landed, update the GA4 section in `CLAUDE.md` to reflect the new schemas in the same PR.
