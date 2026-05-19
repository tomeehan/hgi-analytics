# 004: Combined Klaviyo Revenue (Apr)

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-004-combined-klaviyo-revenue`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes: register the missing Klaviyo Bronze sources, extend the existing Klaviyo staging models to cover all live brands, add a new `stg_klaviyo__placed_orders` model that filters `events` to `event_type = 'Placed Order'`, and add a new `fct_klaviyo_revenue` Gold model that unifies campaign attributed and flow attributed revenue with `store_id` and `order_month`. Then `cd dbt && dbt build --select fct_klaviyo_revenue+` and confirm tests pass.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration combined_klaviyo_revenue`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-004-combined-klaviyo-revenue`.
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
     - For the new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert the returned value equals **190834** (rounded GBP, per the PDF).
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
- Page 1 (cover), rightmost hero KPI, label "COMBINED KLAVIYO REVENUE".
- April 2026 value (PDF): **£190,834**, with footnote "Placed Order, 5-day window".
- Per brand breakdown (from each brand's CRM Performance page, totals are campaign + flow):
  - Revitalash (page 8): total £117,528 (campaign £84,212 + flow £33,316).
  - iS Clinical (page 16): total £64,885 (campaign £50,667 + flow £14,218).
  - Deese PRO (page 23): total £7,798 (campaign £2,330 + flow £5,468).
  - HGI (page 28): total £623 (campaign £15 + flow £608).
  - Sum: £117,528 + £64,885 + £7,798 + £623 = £190,834. Matches the cover.
- Source of truth: per the PDF appendix on page 31, Klaviyo "Placed Order, 5-day attribution window" provides campaign + flow revenue, opens, clicks, profile counts.
- March 2026 value: not on the PDF cover. Capture from the Lightdash API at verification time and write into the Basecamp comment.

## Metric definition

The total Klaviyo-attributed revenue for the selected calendar month, summed across the selected brands. "Klaviyo-attributed revenue" is the sum of `value` on Klaviyo `Placed Order` events whose attribution chain points back to either a Klaviyo campaign send or a Klaviyo flow message within the 5-day window (Klaviyo's default attribution model). This combines what the PDF per-brand pages split into "Campaign Rev" and "Flow Rev" into a single hero figure.

- Source of truth: Klaviyo Events API (via Airbyte). Klaviyo emits one `Placed Order` event per attributed order; the event payload carries `$campaign_id` and/or `$flow_id` under `attributes.event_properties`, plus `value` (order total in the brand's currency).
- Attribution: Klaviyo Placed Order, 5-day click window. The attribution itself is done inside Klaviyo before the event lands in Bronze, so dbt does not re-implement it; we just sum `value` on events that have a non-null `campaign_id` or `flow_id`.
- Currency: GBP. All four Klaviyo accounts settle in GBP, so `value` is treated as already GBP. Mirrors the GBP assumption made by tickets 001 and 003. Revisit if a non-GBP Klaviyo account is added.
- Filter behaviour:
  - **Month filter** changes which month's events are summed (via `order_month = date_trunc('month', occurred_at)`).
  - **Brand filter** = All sums across every loaded Klaviyo account. A specific brand value filters to that account only. Brands with no data for the month show £0 (the "filter does not switch the view, only the data" behaviour from generator section (d)).

## Data dependencies

### Bronze sources
- Live `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` (already a declared dbt source).
- Live `BRONZE_KLAVIYO_DEESE_PRO.EVENTS` (already a declared dbt source).
- Live `BRONZE_KLAVIYO_REVITALASH.EVENTS` (Bronze schema is loaded per `CLAUDE.md` and the data availability map, but **not yet declared in `dbt/models/bronze/_sources.yml`** as of writing). Add it.
- Partial `BRONZE_KLAVIYO_HARPER_GRACE.EVENTS` (declared as a source, but per `CLAUDE.md` and `airbyte/README.md` the connection emits records yet no destination tables get written). Per the PDF this brand contributes only £623 of £190,834 (0.3%), so its absence is a small caveat, not a blocker. Document the gap in the verification comment.
- Blocked `BRONZE_KLAVIYO_GESKE` (schema exists, no sync configured). PDF does not break Geske out for Klaviyo, so this is acceptable.

### Silver / Gold models
- `dbt/models/silver/stg_klaviyo__events.sql` exists, but **only unions iSC and Deese PRO**. The file selects `event_id`, `event_type`, `occurred_at`, `value`, `value_currency`, `campaign_id`, `flow_id`, `message_id`, `profile_id`, `store_id`. Revitalash and Harper Grace need to be added to the union.
- `dbt/models/silver/stg_klaviyo__campaigns.sql` and `stg_klaviyo__campaign_stats.sql` similarly union only iSC + Deese. **They are not on this ticket's critical path** (tickets 017, 018, 019 will need them), but extending them now is cheap; do so to keep all Klaviyo staging models on the same brand list. If touching them is out of scope, leave them alone and let a later ticket handle it.
- `dbt/models/gold/fct_campaign_performance.sql` exists. It only covers **campaign-attributed** revenue (joins `stg_klaviyo__campaign_stats` to `stg_klaviyo__campaigns`). It does **not** cover flow-attributed revenue. It also does not surface an `order_month` dimension matching the dashboard filter convention. This ticket does not modify it; it builds a parallel `fct_klaviyo_revenue` model purpose-built for the combined hero KPI.
- **No existing Gold model unifies campaign + flow revenue.** This ticket creates one.

### New models required
- `dbt/models/silver/stg_klaviyo__placed_orders.sql` (new): filters `stg_klaviyo__events` to `event_type = 'Placed Order'`, exposes `event_id`, `store_id`, `occurred_at`, `order_month` (`date_trunc('month', occurred_at)::date`), `value`, `campaign_id`, `flow_id`, and a derived `attribution_kind` column (`'campaign'` if `campaign_id is not null`, else `'flow'` if `flow_id is not null`, else `'unattributed'`).
- `dbt/models/gold/fct_klaviyo_revenue.sql` (new): one row per Placed Order event with a campaign or flow attribution. Columns: `event_id` (PK), `store_id`, `order_month`, `occurred_at`, `revenue` (renamed from `value`), `attribution_kind`, `campaign_id`, `flow_id`. Filter out `attribution_kind = 'unattributed'` so a `sum(revenue)` produces the Klaviyo-attributed number that matches the PDF.

## dbt work

This is the bulk of the ticket.

1. **Register the missing Bronze source** in `dbt/models/bronze/_sources.yml`:
   ```yaml
   - name: bronze_klaviyo_revitalash
     database: HGI
     schema: BRONZE_KLAVIYO_REVITALASH
     tables:
       - name: events
       - name: campaigns
       - name: campaign_values_reports
       - name: profiles
   ```
   `bronze_klaviyo_harper_grace` is already declared.

2. **Extend `dbt/models/silver/stg_klaviyo__events.sql`** to union all four brands. Current file has two CTEs (`isclinical`, `deese_pro`) plus a `unioned` CTE. Add `revitalash` and `harper_grace` CTEs with the same shape (`'revitalash'` / `'harper_grace'` as `store_id`), referencing `{{ source('bronze_klaviyo_revitalash', 'events') }}` and `{{ source('bronze_klaviyo_harper_grace', 'events') }}`. The Harper Grace CTE will likely return zero rows today (per the partial-sync caveat above) but is harmless to include and will start contributing once the Airbyte gap is fixed.

3. **Create `dbt/models/silver/stg_klaviyo__placed_orders.sql`** (new):
   ```sql
   with events as (
       select * from {{ ref('stg_klaviyo__events') }}
       where event_type = 'Placed Order'
   ),

   shaped as (
       select
           event_id,
           store_id,
           occurred_at,
           date_trunc('month', occurred_at)::date as order_month,
           value::float                            as revenue,
           campaign_id,
           flow_id,
           case
               when campaign_id is not null then 'campaign'
               when flow_id is not null     then 'flow'
               else 'unattributed'
           end as attribution_kind
       from events
   )

   select * from shaped
   ```

4. **Create `dbt/models/gold/fct_klaviyo_revenue.sql`** (new):
   ```sql
   select
       event_id,
       store_id,
       order_month,
       occurred_at,
       revenue,
       attribution_kind,
       campaign_id,
       flow_id
   from {{ ref('stg_klaviyo__placed_orders') }}
   where attribution_kind in ('campaign', 'flow')
   ```
   Keep both campaign and flow rows so a future ticket can break them out via the `attribution_kind` dimension without rebuilding the model.

5. **Update `dbt/models/silver/_schema.yml`** for `stg_klaviyo__events` (description should say "unioned across isClinical, Deese Pro, Revitalash, and Harper Grace") and add a new entry for `stg_klaviyo__placed_orders`:
   ```yaml
   - name: stg_klaviyo__placed_orders
     description: "Klaviyo Placed Order events with attribution kind (campaign / flow / unattributed)."
     columns:
       - name: event_id
         tests:
           - not_null
           - unique
       - name: store_id
         tests:
           - not_null
       - name: order_month
         tests:
           - not_null
   ```

6. **Update `dbt/models/gold/_schema.yml`** with a `fct_klaviyo_revenue` entry that wires up the dashboard filter convention from ticket 001:
   ```yaml
   - name: fct_klaviyo_revenue
     description: "Klaviyo Placed Order revenue, attributed to a campaign or a flow within the 5-day window. Grain: one row per Placed Order event."
     meta:
       label: "Klaviyo Revenue"
     columns:
       - name: event_id
         tests:
           - not_null
           - unique
       - name: store_id
         description: "Brand identifier."
         tests:
           - not_null
         meta:
           dimension:
             label: "Brand"
             sql: "case ${TABLE}.store_id when 'revitalash' then 'Revitalash' when 'isclinical' then 'iS Clinical' when 'deese_pro' then 'Deese PRO' when 'harper_grace' then 'Harper Grace' when 'geske' then 'Geske' else ${TABLE}.store_id end"
       - name: order_month
         description: "First day of the month the Placed Order event occurred."
         tests:
           - not_null
       - name: revenue
         description: "Order value attributed to Klaviyo (5-day window)."
         meta:
           metrics:
             total_klaviyo_revenue:
               type: sum
               label: "Klaviyo Revenue"
               format: "gbp"
               round: 0
         tests:
           - dbt_utils.accepted_range:
               min_value: 0
       - name: attribution_kind
         description: "campaign or flow."
       - name: campaign_id
         description: "Klaviyo campaign ID, null for flow-attributed events."
       - name: flow_id
         description: "Klaviyo flow ID, null for campaign-attributed events."
   ```

7. **Build and test:**
   ```bash
   cd dbt && dbt deps && dbt build --select fct_klaviyo_revenue+
   ```
   Expected: `sum(revenue) where order_month = '2026-04-01'` should land near £190,211 (PDF total £190,834 minus the £623 Harper Grace contribution that won't be in Bronze yet). If iSC / Deese / RL each match their PDF per-brand totals to within rounding, the model is correct and the only gap is the Harper Grace Airbyte sync.

## Lightdash work

A single big number tile on the **Group Overview** dashboard, fourth in the top row of cover KPIs (rightmost position, after Combined Shopify Revenue, Combined Shopify Orders, and Combined Meta Spend).

- **Tile type:** big number.
- **Label:** "Combined Klaviyo Revenue".
- **Underlying explore:** `fct_klaviyo_revenue`.
- **Metric:** `total_klaviyo_revenue` (`sum(revenue)`, GBP, 0 dp).
- **Filter wiring:** the dashboard level **Brand** and **Month** filters from ticket 001 auto apply, because `fct_klaviyo_revenue` exposes `store_id` (with the same label/rename map as `fct_orders` and `fct_ad_spend`) and `order_month`. Confirm by reading the dbt manifest after building, then by toggling the filter in the live dashboard after deploying.

Migration filename: produced by `bin/new-lightdash-migration combined_klaviyo_revenue` (yields `lightdash/migrations/YYYYMMDD_HHMMSS_combined_klaviyo_revenue.py`). The migration must:
- Create the saved chart (saved on the project, not embedded in dashboard) targeting `fct_klaviyo_revenue` with `sum(revenue)`.
- Attach a new big number tile to dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`, positioned in the cover KPI row (rightmost).
- Be idempotent / re-runnable safe per `lightdash/migrations/README.md`. Support `--dry-run`.
- Print the new chart UUID and tile UUID so they can be slotted into the verification snippet.

## API verification snippet

Run this in step 8 of the workflow above. The exact field IDs come from Lightdash's auto generated identifiers; check the explore via `GET /api/v1/projects/<project-uuid>/explores/fct_klaviyo_revenue` if the names below don't match.

```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"
EXPECTED_APRIL = 190834

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace `<chart-uuid>` after the migration prints it.
results = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_klaviyo_revenue_order_month"}, "operator": "equals", "values": ["2026-04-01"]},
    ]},
})
got = round(results["rows"][0]["fct_klaviyo_revenue_total_klaviyo_revenue"]["value"]["raw"])
# Soft assertion: the live figure will be ~£190,211 until Harper Grace Klaviyo sync is fixed.
# Expect a small (≤£700) shortfall vs the PDF; log both numbers in the Basecamp comment.
print(f"April live: {got}, PDF expected: {EXPECTED_APRIL}, delta: {EXPECTED_APRIL - got}")
assert abs(EXPECTED_APRIL - got) < 1000, f"April mismatch larger than HGI gap: got {got}, expected {EXPECTED_APRIL}"

# March, for the Basecamp comment + filter change validation.
results_mar = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_klaviyo_revenue_order_month"}, "operator": "equals", "values": ["2026-03-01"]},
    ]},
})
got_mar = round(results_mar["rows"][0]["fct_klaviyo_revenue_total_klaviyo_revenue"]["value"]["raw"])
print(f"March: {got_mar}")
```

If the saved chart doesn't exist yet (early in the migration), use `POST /api/v1/projects/<projectUuid>/explores/fct_klaviyo_revenue/runQuery` against the explore directly with the same filter shape.

## Snowflake fallback SQL

If the API path fails or disagrees with the PDF, reproduce the number directly from Snowflake (`snow sql -c hgi`):

```sql
-- April 2026: combined Klaviyo-attributed revenue across all live brands.
select sum(revenue) as combined_klaviyo_revenue
from HGI.GOLD.FCT_KLAVIYO_REVENUE
where order_month = '2026-04-01';

-- April 2026: per brand breakdown (sanity check against PDF per-brand CRM pages).
select store_id, round(sum(revenue), 0) as revenue_gbp
from HGI.GOLD.FCT_KLAVIYO_REVENUE
where order_month = '2026-04-01'
group by 1
order by 2 desc;

-- April 2026: campaign vs flow split (sanity check against PDF CRM KPI strips).
select store_id, attribution_kind, round(sum(revenue), 0) as revenue_gbp
from HGI.GOLD.FCT_KLAVIYO_REVENUE
where order_month = '2026-04-01'
group by 1, 2
order by 1, 2;

-- March 2026: combined (for filter change validation).
select sum(revenue) as combined_klaviyo_revenue
from HGI.GOLD.FCT_KLAVIYO_REVENUE
where order_month = '2026-03-01';
```

Expected April breakdown (per PDF, totals are campaign + flow):
- Revitalash £117,528 (£84,212 + £33,316)
- iS Clinical £64,885 (£50,667 + £14,218)
- Deese PRO £7,798 (£2,330 + £5,468)
- Harper Grace £623 (£15 + £608), absent today due to the Klaviyo destination-table gap.
- Total: £190,834 (PDF); live target ≈ £190,211 until Harper Grace Klaviyo sync is fixed.

## Post deploy ops (paste into the PR description)
> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_combined_klaviyo_revenue.py` (step 7).

(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed

This ticket extends the Klaviyo staging models from a 2-brand union to a 4-brand union (adding Revitalash and Harper Grace) and introduces a new Gold model (`fct_klaviyo_revenue`) that unifies campaign + flow attribution. `CLAUDE.md` already documents the Klaviyo brand list under "Klaviyo accounts", so no factual update is strictly required, but:

- Add a brief mention under "Gold layer" that `fct_klaviyo_revenue` is the canonical source for combined campaign + flow Klaviyo revenue, distinct from `fct_campaign_performance` which is campaign-only.
- If the Harper Grace Klaviyo gap is closed during this ticket's lifetime, update the "Klaviyo accounts" bullet to remove the "no destination tables get written" caveat.
