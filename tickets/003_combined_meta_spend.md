# 003: Combined Meta Spend (Apr)

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-003-combined-meta-spend`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes: extend `stg_meta__ads_spend` to union all 3 Meta accounts (Revitalash, iS Clinical, Deese PRO), add `order_month`, register the missing Bronze sources, then run `cd dbt && dbt build --select fct_ad_spend+` and confirm tests pass.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration combined_meta_spend`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-003-combined-meta-spend`.
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
     - For the new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert the returned value equals **22581** (rounded GBP, per the PDF).
     - Repeat the API query with Month=March-2026 to capture the March value (needed for the Basecamp comment, and proves the month filter works end to end).
9. **Close the loop on Basecamp.**
   - Add a comment to the card with:
     - the merged PR URL,
     - the verified April and March values (from step 8),
     - the dashboard tile UUID you just created,
     - any caveats or known gaps (especially if the live number does not match the PDF, link the prerequisite ticket).
   - Move the card from **In progress** to **Done**.
10. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page 1 (cover), third hero KPI from the left, label "COMBINED META SPEND".
- April 2026 value (PDF): **£22,581**, footnote "3 accounts (RL, ISC, Deesse)".
- Page 2 sub box "META SPEND SHARE BY BRAND" gives the breakdown: Revitalash £14,467, iS Clinical £7,657, Deese PRO £457, Harpar Grace no spend. £14,467 + £7,657 + £457 = £22,581 confirms the total.
- March 2026 value: not on the PDF cover. Capture from the Lightdash API at verification time and write into the Basecamp comment.

## Metric definition

Total Meta (Facebook Marketing) ad spend for the selected calendar month, summed across the selected brands. "Spend" is the unmodified `spend` field from the Meta Marketing API (`ads_insights` daily aggregation), reported in GBP because all three ad accounts settle in GBP.

- Source of truth: Meta Marketing API via Airbyte, landing in `BRONZE_META_<BRAND>.ADS_INSIGHTS`.
- Attribution: not relevant for spend. Spend is spend, regardless of attribution window. The 7 day click + 1 day view note on the PDF page 2 sub box applies to spend share calculation as displayed, but the spend number itself is the same under any attribution model (Meta charges for impressions/clicks, not for attributed conversions). Attribution windows only matter for revenue, which is a separate ticket (007).
- Currency: GBP. All three Meta ad accounts (iS Clinical, Deese Pro, Revitalash) report in GBP, so the `spend` column is treated as already GBP.
- Filter behaviour:
  - **Month filter** changes which month's spend is summed (via `order_month = date_trunc('month', spend_date)`).
  - **Brand filter** = All sums across all three loaded Meta accounts. A specific brand value filters to that account only.

## Data dependencies

### Bronze sources
- Live `BRONZE_META_ISCLINICAL.ADS_INSIGHTS` (already a declared dbt source).
- Live `BRONZE_META_DEESE_PRO.ADS_INSIGHTS` (Bronze schema is loaded per `CLAUDE.md` and the data availability map, but **not yet declared in `dbt/models/bronze/_sources.yml`** as of writing).
- Live `BRONZE_META_REVITALASH.ADS_INSIGHTS` (same caveat: Bronze loaded, source declaration missing).

### Silver / Gold models
- `dbt/models/silver/stg_meta__ads_spend.sql` exists, but **only reads from `bronze_meta_isclinical`**. Its CTE structure has a single `isclinical` branch and `unioned as (select * from isclinical)`. This ticket extends it to union all three brands.
- `dbt/models/gold/fct_ad_spend.sql` is a thin pass through (`select * from {{ ref('stg_meta__ads_spend') }}`). No structural change needed in the Gold file itself, but it inherits the new rows once Silver is extended.
- `dbt/models/gold/_schema.yml` already declares `fct_ad_spend` with a `total_meta_spend` metric (`sum(spend)`) and a `store_id` dimension. **Add the `order_month` column** (description, no test required beyond the existing ones) so the dashboard's Month filter can target it.

### New columns required
- `order_month` (date, first day of the month) on `stg_meta__ads_spend` and therefore on `fct_ad_spend`. Computed as `date_trunc('month', spend_date)`.

### Cross ticket dependency
- **Ticket 007 (Meta spend share by brand) depends on this ticket.** Ticket 007 needs `fct_ad_spend` to contain all three brands' spend so its breakdown bar chart works. 003 must merge before 007 can verify its numbers. Add a note in the 007 ticket if it hasn't been written yet.

## dbt work

This is the bulk of the ticket.

1. **Register the missing Bronze sources** in `dbt/models/bronze/_sources.yml`:
   ```yaml
   - name: bronze_meta_deese_pro
     database: HGI
     schema: BRONZE_META_DEESE_PRO
     tables:
       - name: ads_insights

   - name: bronze_meta_revitalash
     database: HGI
     schema: BRONZE_META_REVITALASH
     tables:
       - name: ads_insights
   ```
2. **Extend `dbt/models/silver/stg_meta__ads_spend.sql`** to union all three brands. The current file builds a single `isclinical` CTE off three day level subqueries (`base_daily`, `purchases_daily`, `purchase_value_daily`). Refactor into a per brand pattern using a Jinja loop or three explicit CTE trios:

   - For each brand `(isclinical, deese_pro, revitalash)`:
     - Build the daily `base`, `purchases`, `purchase_value` CTEs off `{{ source('bronze_meta_<brand>', 'ads_insights') }}`.
     - Produce a per brand CTE that selects `spend_date`, `'<brand>' as store_id`, and the daily aggregates.
   - Union all three.
   - Add `date_trunc('month', spend_date) as order_month` to the final select.

   A clean Jinja loop version is preferable to repeated CTEs (mirrors the spirit of `stg_shopify__orders`, though that one uses explicit CTEs per `CLAUDE.md`'s multi brand union convention; either is fine here as long as it's readable).

3. **Update `dbt/models/silver/_schema.yml`** for `stg_meta__ads_spend`:
   - Add `order_month` with description "First day of the month spend was recorded (date_trunc month of spend_date)".
   - Keep existing `not_null` test on `store_id` and `spend_date`.
   - Add a `dbt_utils.accepted_range` test on `spend` with `min_value: 0` (spend should never be negative).

4. **Update `dbt/models/gold/_schema.yml`** for `fct_ad_spend`:
   - Add `order_month` column entry.
   - Add the `store_id` value rename map (matching the convention from ticket 001 for `fct_orders`):
     ```yaml
     meta:
       dimension:
         label: "Brand"
         sql: "case ${TABLE}.store_id when 'revitalash' then 'Revitalash' when 'isclinical' then 'iS Clinical' when 'deese_pro' then 'Deese PRO' when 'geske' then 'Geske' else ${TABLE}.store_id end"
     ```
   - Confirm `total_meta_spend` metric (`sum(spend)`, format gbp, round 0) is wired correctly.

5. **Build and test:**
   ```bash
   cd dbt && dbt deps && dbt build --select fct_ad_spend+
   ```
   Expected: ~30 rows in `fct_ad_spend` for April 2026 (one row per brand per day, 30 days × 3 brands), `sum(spend) where order_month = '2026-04-01'` close to 22,581 (the PDF target).

## Lightdash work

A single big number tile on the **Group Overview** dashboard, third in the top row of cover KPIs (after "Combined Shopify Revenue" from ticket 001 and "Combined Shopify Orders" from ticket 002).

- **Tile type:** big number.
- **Label:** "Combined Meta Spend".
- **Underlying explore:** `fct_ad_spend`.
- **Metric:** `total_meta_spend` (`sum(spend)`, GBP, 0 dp).
- **Filter wiring:** the dashboard level **Brand** and **Month** filters from ticket 001 auto apply, because `fct_ad_spend` now exposes `store_id` (with the same label/rename map as `fct_orders`) and `order_month`. Confirm by reading the dbt manifest after building, then by toggling the filter in the live dashboard after deploying.

Migration filename: produced by `bin/new-lightdash-migration combined_meta_spend` (yields `lightdash/migrations/YYYYMMDD_HHMMSS_combined_meta_spend.py`). The migration must:
- Create the saved chart (saved on the project, not embedded in dashboard) targeting `fct_ad_spend` with `sum(spend)`.
- Attach a new big number tile to dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`, positioned in the cover KPI row.
- Be idempotent / re-runnable safe per `lightdash/migrations/README.md`. Support `--dry-run`.
- Print the new chart UUID and tile UUID so they can be slotted into the verification snippet.

## API verification snippet

Run this in step 8 of the workflow above. The exact field IDs come from Lightdash's auto generated identifiers; check the explore via `GET /api/v1/projects/<project-uuid>/explores/fct_ad_spend` if the names below don't match.

```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"
EXPECTED_APRIL = 22581

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace <chart-uuid> after the migration prints it
results = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_ad_spend_order_month"}, "operator": "equals", "values": ["2026-04-01"]},
    ]},
})
got = round(results["rows"][0]["fct_ad_spend_total_meta_spend"]["value"]["raw"])
assert got == EXPECTED_APRIL, f"April mismatch: got {got}, expected {EXPECTED_APRIL}"
print(f"April OK: {got}")

# March, for the Basecamp comment + filter change validation
results_mar = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_ad_spend_order_month"}, "operator": "equals", "values": ["2026-03-01"]},
    ]},
})
got_mar = round(results_mar["rows"][0]["fct_ad_spend_total_meta_spend"]["value"]["raw"])
print(f"March: {got_mar}")
```

If the saved chart doesn't exist yet (early in the migration), use `POST /api/v1/projects/<projectUuid>/explores/fct_ad_spend/runQuery` against the explore directly with the same filter shape.

## Snowflake fallback SQL

If the API path fails or disagrees with the PDF, reproduce the number directly from Snowflake (`snow sql -c hgi`):

```sql
-- April 2026: combined Meta spend across all 3 accounts
select sum(spend) as combined_meta_spend
from HGI.GOLD.FCT_AD_SPEND
where date_trunc('month', spend_date) = '2026-04-01';

-- April 2026: per brand breakdown (sanity check against PDF page 2 sub box)
select store_id, round(sum(spend), 0) as spend_gbp
from HGI.GOLD.FCT_AD_SPEND
where date_trunc('month', spend_date) = '2026-04-01'
group by 1
order by 2 desc;

-- March 2026: combined (for filter change validation)
select sum(spend) as combined_meta_spend
from HGI.GOLD.FCT_AD_SPEND
where date_trunc('month', spend_date) = '2026-03-01';
```

Expected April breakdown (per PDF page 2): Revitalash £14,467, iS Clinical £7,657, Deese PRO £457. Total £22,581.

## Post deploy ops (paste into the PR description)
> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_combined_meta_spend.py` (step 7).

(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed

This ticket extends `stg_meta__ads_spend` from a single brand staging model to a 3 brand union, mirroring the multi brand Shopify/Klaviyo union convention. `CLAUDE.md` already lists three Meta connections under "Meta (Facebook Marketing) connections", so no factual update is strictly required, but consider adding a sentence under "Conventions" noting that the multi brand union pattern now extends to Meta (`stg_meta__ads_spend`), so a future Claude touching it knows to add new ad accounts to the same union.
