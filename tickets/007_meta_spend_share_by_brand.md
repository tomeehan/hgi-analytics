# 007: Meta spend share by brand

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-007-meta-spend-share-by-brand`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes: none. This ticket is unblocked by ticket 003's `stg_meta__ads_spend` extension, which adds the per brand union, `order_month`, and the `store_id` rename map on `fct_ad_spend`. Confirm ticket 003 has merged before starting. If not, stop and pick up 003 first.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration meta_spend_share_by_brand`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-007-meta-spend-share-by-brand`.
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
     - For the new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert the returned rows match the PDF: Revitalash 14467, iS Clinical 7657, Deese PRO 457, Harpar Grace 0 (no spend / not present as a Meta account, see "Data dependencies").
     - Repeat the API query with Month=March-2026 to capture the March per brand values (needed for the Basecamp comment, and proves the month filter works end to end).
9. **Close the loop on Basecamp.**
   - Add a comment to the card with:
     - the merged PR URL,
     - the verified April and March per brand values (from step 8),
     - the dashboard tile UUID you just created,
     - any caveats or known gaps (especially if the live numbers do not match the PDF, link the prerequisite ticket 003).
   - Move the card from **In progress** to **Done**.
10. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page 2 (Cross brand summary), bottom right sub box titled "META SPEND SHARE BY BRAND", subtitle "7-day click + 1-day view".
- April 2026 per brand values (PDF):
  - Revitalash **£14,467**
  - iS Clinical **£7,657**
  - Deese PRO **£457**
  - Harpar Grace **no spend**
- Total: £22,581 (matches the page 1 "Combined Meta Spend" hero KPI, see ticket 003).
- March 2026 values: not in the PDF; capture from the Lightdash API at verification time and write them into the Basecamp comment.

Note: despite the title "META SPEND SHARE BY BRAND", the PDF box lists absolute £ per brand, not percentages. The chart should mirror that: show absolute £ per brand (which trivially conveys the share). Do not compute a percentage column.

## Metric definition

Total Meta (Facebook Marketing) ad spend per brand for the selected calendar month. "Spend" is the unmodified `spend` field from the Meta Marketing API (`ads_insights` daily aggregation), reported in GBP because all three ad accounts settle in GBP. The PDF's "7-day click + 1-day view" subtitle refers to Meta's revenue attribution window: it applies to attributed revenue (purchases / purchase value), not to spend. Spend is spend regardless of attribution model (Meta charges for impressions / clicks, not for attributed conversions). The subtitle is included verbatim on the tile only for symmetry with the PDF.

- Source of truth: Meta Marketing API via Airbyte, landing in `BRONZE_META_<BRAND>.ADS_INSIGHTS`. Same pipeline as ticket 003.
- Currency: GBP. All three Meta ad accounts settle in GBP.
- Filter behaviour:
  - **Month filter** changes which month's spend is summed (via `order_month = date_trunc('month', spend_date)`).
  - **Brand filter** = All shows one bar per loaded brand (3 bars: Revitalash, iS Clinical, Deese PRO). A specific brand value collapses the chart to that single bar; the other brands' bars drop to £0 but remain visible, per the layout decision in generator section (d) ("filter does not switch the view, only the data").

## Data dependencies

### Bronze sources
- Live `BRONZE_META_ISCLINICAL.ADS_INSIGHTS`.
- Live `BRONZE_META_DEESE_PRO.ADS_INSIGHTS`.
- Live `BRONZE_META_REVITALASH.ADS_INSIGHTS`.

All 3 Meta Bronze schemas are populated per the data availability map in `tickets/_ticket_generator.md` section (c).

### Silver / Gold models
- `dbt/models/silver/stg_meta__ads_spend.sql`. As of the writing of this ticket, this model **only reads from `bronze_meta_isclinical`**. Its CTE structure has a single `isclinical` branch and `unioned as (select * from isclinical)`, with no `order_month` column. Ticket 003 extends it to union all three brands and adds `order_month`.
- `dbt/models/gold/fct_ad_spend.sql`. Thin pass through (`select * from {{ ref('stg_meta__ads_spend') }}`). Inherits whatever Silver provides.
- `dbt/models/gold/_schema.yml`. Declares `fct_ad_spend` with a `total_meta_spend` metric (`sum(spend)`, GBP, 0 dp) and a `store_id` dimension. Ticket 003 adds the `order_month` column and the `store_id` value rename map.

### Cross ticket dependency (prerequisite)
- **This ticket depends on ticket 003 (`003: Combined Meta Spend (Apr)`).** Ticket 003 extends `stg_meta__ads_spend` to union all 3 Meta accounts, adds `order_month` and the `store_id` rename map on `fct_ad_spend`. Without 003 merged, `fct_ad_spend` contains only iS Clinical spend, so this ticket's chart would render two empty bars (Revitalash, Deese PRO) and would not verify against the PDF.
- **Ticket 003 must merge before ticket 007 can verify against the PDF.** If 003 is still open when this ticket is picked up, stop and pick up 003 first.

### Harpar Grace caveat
The PDF lists "Harpar Grace no spend". There is no Meta ad account connected for Harpar Grace at all (only the 3 brands listed in `CLAUDE.md` under "Meta (Facebook Marketing) connections"). The bar chart will therefore show 3 bars, not 4. The "no spend" label on the PDF is consistent with this (a 4th bar at £0 would be visually equivalent). Note this in the Basecamp verification comment, no separate prerequisite ticket needed.

## dbt work

**No dbt changes of its own.** This ticket is unblocked by ticket 003's `stg_meta__ads_spend` extension, which adds the per brand union, `order_month`, and the `store_id` rename map on `fct_ad_spend`. Confirm by reading the manifest after ticket 003 has merged (or by querying `HGI.GOLD.FCT_AD_SPEND` directly and checking that `store_id` has 3 distinct values and `order_month` exists).

If ticket 003 has not merged yet, stop and pick up 003 first.

## Lightdash work

A single **horizontal bar chart** tile on the **Group Overview** dashboard, positioned on page 2 of the dashboard layout next to the (future) ticket 006 tile "GA4 revenue share by brand", mirroring the PDF page 2 bottom row sub boxes.

- **Tile type:** horizontal bar chart (`flipAxes: true`). Per the user's standing preference recorded in project memory `feedback_lightdash_horizontal_bars.md`: default to horizontal bar charts in Lightdash for category bars, vertical only for time series. This is a category bar chart (one bar per brand) so it must be horizontal.
- **Tile label:** "Meta spend share by brand".
- **Tile subtitle (markdown under the title, or the chart's description):** "7-day click + 1-day view (attribution applies to revenue not spend; included for symmetry with the PDF)".
- **Underlying explore:** `fct_ad_spend`.
- **X axis (post flip):** the category axis showing `store_id` (rendered as the human readable brand name via the rename map from ticket 003).
- **Y axis (post flip):** the value axis showing `sum(spend)` (metric `total_meta_spend`, format gbp, round 0).
- **Sort:** by `sum(spend)` desc, so the longest bar (Revitalash) appears at the top.
- **Filter wiring:** the dashboard level **Brand** and **Month** filters from ticket 001 auto apply, because `fct_ad_spend` exposes `store_id` (with the same label/rename map as `fct_orders`) and `order_month` (both added by ticket 003). Confirm by reading the dbt manifest after ticket 003's build, then by toggling the filter in the live dashboard after deploying.

Migration filename: produced by `bin/new-lightdash-migration meta_spend_share_by_brand` (yields `lightdash/migrations/YYYYMMDD_HHMMSS_meta_spend_share_by_brand.py`). The migration must:

- Create the saved chart (saved on the project, not embedded in dashboard) targeting `fct_ad_spend` with `sum(spend)` grouped by `store_id`, configured as a horizontal bar chart (`flipAxes: true`), sorted by `sum(spend)` desc.
- Attach a new chart tile to dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`, positioned next to the (future) GA4 revenue share tile from ticket 006.
- Be idempotent / re-runnable safe per `lightdash/migrations/README.md`. Support `--dry-run`.
- Print the new chart UUID and tile UUID so they can be slotted into the verification snippet.

## API verification snippet

Run this in step 8 of the workflow above. The exact field IDs come from Lightdash's auto generated identifiers; check the explore via `GET /api/v1/projects/<project-uuid>/explores/fct_ad_spend` if the names below don't match.

```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"
EXPECTED_APRIL = {
    "revitalash": 14467,
    "isclinical": 7657,
    "deese_pro": 457,
    # Harpar Grace: no Meta account, no row expected
}

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace `<chart-uuid>` after the migration prints it
results = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_ad_spend_order_month"}, "operator": "equals", "values": ["2026-04-01"]},
    ]},
})

actual = {}
for row in results["rows"]:
    brand = row["fct_ad_spend_store_id"]["value"]["raw"]
    spend = round(row["fct_ad_spend_total_meta_spend"]["value"]["raw"])
    actual[brand] = spend
print("April per brand:", actual)

for brand, expected in EXPECTED_APRIL.items():
    got = actual.get(brand, 0)
    assert got == expected, f"{brand} April mismatch: got {got}, expected {expected}"
print("April per brand OK")

# March, for the Basecamp comment + filter change validation
results_mar = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_ad_spend_order_month"}, "operator": "equals", "values": ["2026-03-01"]},
    ]},
})
march = {}
for row in results_mar["rows"]:
    brand = row["fct_ad_spend_store_id"]["value"]["raw"]
    spend = round(row["fct_ad_spend_total_meta_spend"]["value"]["raw"])
    march[brand] = spend
print("March per brand:", march)
```

If the saved chart doesn't exist yet (early in the migration), use `POST /api/v1/projects/<projectUuid>/explores/fct_ad_spend/runQuery` against the explore directly with the same filter shape.

## Snowflake fallback SQL

If the API path fails or disagrees with the PDF, reproduce the numbers directly from Snowflake (`snow sql -c hgi`):

```sql
-- April 2026: per brand Meta spend (verifies against PDF page 2 sub box)
select store_id, round(sum(spend), 0) as spend_gbp
from HGI.GOLD.FCT_AD_SPEND
where date_trunc('month', spend_date) = '2026-04-01'
group by 1
order by 2 desc;

-- March 2026: per brand Meta spend (for filter change validation)
select store_id, round(sum(spend), 0) as spend_gbp
from HGI.GOLD.FCT_AD_SPEND
where date_trunc('month', spend_date) = '2026-03-01'
group by 1
order by 2 desc;
```

Expected April per brand (per PDF page 2): Revitalash £14,467, iS Clinical £7,657, Deese PRO £457. Total £22,581 (matches ticket 003's hero KPI).

## Post deploy ops (paste into the PR description)
> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_meta_spend_share_by_brand.py` (step 7).

(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed

No new sources, schemas, roles, or conventions are introduced by this ticket (it's a pure Lightdash tile addition on top of ticket 003's groundwork). No `CLAUDE.md` update required.
