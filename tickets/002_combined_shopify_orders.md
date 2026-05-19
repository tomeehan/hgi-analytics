# 002: Combined Shopify Orders (Apr)

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-002-combined_shopify_orders`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes (if any): no dbt changes needed. `fct_orders` already exposes the `order_count` metric (`count_distinct` on `order_id`) plus `store_id` and `order_month`. Confirm by reading `dbt/models/gold/_schema.yml` before writing the migration.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration combined_shopify_orders`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-002-combined_shopify_orders`.
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
     - For each new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert the returned value equals the expected April number from this ticket.
     - Repeat the API query with Month=March-2026 to capture the March value (needed for the Basecamp comment, and proves the month filter works end to end).
9. **Close the loop on Basecamp.**
   - Add a comment to the card with:
     - the merged PR URL,
     - the verified April and March values (from step 8),
     - the dashboard tile UUIDs you just created,
     - any caveats or known gaps (especially if the live number does not match the PDF, link the prerequisite ticket).
   - Move the card from **In progress** to **Done**.
10. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page 1 (cover), second hero KPI from the left, label "COMBINED SHOPIFY ORDERS (APR)".
- April 2026 value (PDF): **3,791** (incl HGI), or **3,764** excluding HGI, with footnote breakdown "RL 2,669 + ISC 1,075 + Deese 20 + HGI 27".
- March 2026 value: not on the PDF cover. Capture from the Lightdash API at verification time (step 8) and write into the Basecamp comment.

## Metric definition

The count of Shopify orders created in the selected calendar month, summed across the selected brands. Plain `count(*)` on `fct_orders` rows (one row per Shopify order). Currency does not apply (this is a count, not money).

- Source of truth: Shopify Admin API (via Airbyte, Bronze, `fct_orders`). Per the PDF appendix on page 31, Shopify is the order-count source of truth.
- Filter behaviour:
  - **Month filter** changes which month's orders are counted.
  - **Brand filter** = All sums across every loaded store. Brand = a specific store shows only that store's order count (other rows in any per-brand breakdown drop to 0, per the layout decision in generator section (d)).

## Data dependencies

### Bronze sources
- ok `BRONZE_SHOPIFY_REVITALASH.ORDERS`, 5,578 orders all-time, 2,637 in April 2026 (PDF: 2,669, a minor gap of about 32 orders).
- ok (partial scope) `BRONZE_SHOPIFY_DEESE_PRO.ORDERS`, 3,233 orders all-time, 20 in April 2026 (matches PDF exactly).
- blocked `BRONZE_SHOPIFY_ISCLINICAL.ORDERS`, only **175 orders all-time**, earliest 2026-02-26. April 2026 has 29 orders vs the PDF's 1,075. This is the same data gap surfaced in ticket 001. **This ticket cannot reach the PDF's April number until the iSC Shopify sync is fixed.** Link the prerequisite sibling ticket: "Backfill/repair iSC Shopify Airbyte sync, only 175 orders since 2026-02-26" (raised in ticket 001).
- blocked `BRONZE_SHOPIFY_GESKE.ORDERS`, Geske bronze schema exists but no `ORDERS` table, so currently contributes 0 orders. Acceptable for April since the PDF does not break Geske out.
- blocked `BRONZE_SHOPIFY_HARPER_GRACE`, does not exist; harpargrace.com Shopify is not connected at all. The 27 HGI orders on the PDF cover are therefore not reproducible here. Out of scope for this ticket; same prerequisite sibling ticket as 001: "Connect harpargrace.com Shopify to Airbyte".

### Silver / Gold models
- ok `dbt/models/silver/stg_shopify__orders.sql`, already unions all loaded Shopify stores by `store_id`.
- ok `dbt/models/gold/fct_orders.sql` (file path verified: lines 1 to 32 union orders, add refunds, and emit `store_id`, `order_id`, `created_at`, `order_month`). **No dbt changes are needed.**
- ok `dbt/models/gold/_schema.yml`, the `order_count` metric (`count_distinct` of `order_id`, label "Order Count") is already declared on `fct_orders`, and the `store_id` dimension already carries `label: Brand` and the value-rename map (installed by ticket 001).

### Current vs PDF
- Today's combined April 2026 Shopify order count across Bronze: approximately **2,686** (2,637 RL + 29 ISC + 20 Deese) versus the PDF's **3,791** (incl HGI) or **3,764** (excl HGI). The ~1,078 gap is dominated by the iS Clinical sync gap.

## dbt work

No dbt changes needed. `fct_orders` already supports `count(*)` via the existing `order_count` metric (`count_distinct` on `order_id`) and exposes `store_id` and `order_month` for the dashboard filters. If you want to be extra safe, run `dbt build --select fct_orders` to confirm nothing has rotted, then move on.

## Lightdash work

One **big number tile** at the top of the Group Overview dashboard, labelled **"Combined Shopify Orders"**, sitting **just to the right of the Combined Shopify Revenue tile** added by ticket 001 (mirroring the PDF cover layout: Revenue is the first hero KPI, Orders is the second).

- Underlying explore: `fct_orders`.
- Metric: the existing `order_count` metric (`count_distinct` on `order_id`). If the explore's metric labelled "Order Count" is not what you expect, fall back to a custom `count(*)`-style metric pointing at `order_id`, but prefer reusing the declared metric so future schema changes propagate.
- The tile **must** inherit the **Brand** and **Month** dashboard filters added by ticket 001. Confirm by reading the dashboard's `filters` block before writing the migration; if those filters are not yet installed, ticket 001 has not been applied and you should pause and apply it first.

Migration filename: produced by `bin/new-lightdash-migration combined_shopify_orders` (yields `lightdash/migrations/YYYYMMDD_HHMMSS_combined_shopify_orders.py`). The migration must:
- Create the single big-number chart for `order_count` on `fct_orders`.
- Attach the chart as a new tile on dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`, positioned to the right of the Combined Shopify Revenue tile from ticket 001 (read the dashboard's existing `tiles[]` to discover that tile's `x` / `y` / `w` / `h` and place the new tile adjacent on the same row).
- Be idempotent where possible (if the script is re-run, it should not silently duplicate the tile, per the migration pattern in `lightdash/migrations/README.md`).
- Support `--dry-run` so the planned API calls can be reviewed.

## API verification snippet

Run this from the repo root after step 7 of the workflow. EXPECTED_APRIL is the PDF figure; the actual value returned today will be around 2,686 because of the data gaps documented above. The assert is intentionally permissive: log both the expected and the actual, do not block the workflow on a mismatch, surface the gap in the Basecamp comment.

```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"
EXPECTED_APRIL = 3791  # PDF April value, incl HGI. Excl HGI = 3764.

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace <chart-uuid> with the new orders chart's UUID after the migration prints it.
results = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_orders_order_month"}, "operator": "equals", "values": ["2026-04-01"]},
    ]},
})
got = results["rows"][0]["fct_orders_order_count"]["value"]["raw"]  # adjust field id if needed
print(f"April orders: got {got}, PDF expected {EXPECTED_APRIL}")
if got != EXPECTED_APRIL:
    print("Mismatch is expected today (iSC Shopify sync gap, HGI not connected). Surface in Basecamp comment.")

# Repeat for March 2026 to confirm the Month filter wires through. Capture the value
# for the Basecamp comment.
march = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_orders_order_month"}, "operator": "equals", "values": ["2026-03-01"]},
    ]},
})
print("March orders:", march["rows"][0]["fct_orders_order_count"]["value"]["raw"])
```

If the field id on the response payload differs from `fct_orders_order_count`, inspect `results["rows"][0]` once and adjust the path. If the tile's chart does not exist yet at API call time, use `POST /api/v1/projects/<projectUuid>/explores/fct_orders/runQuery` as a fallback.

## Snowflake fallback SQL

If the API path fails or the answer disagrees with the PDF in a way you cannot explain, reproduce the number directly from Snowflake via `snow sql -c hgi`:

```sql
-- Combined April 2026 Shopify order count (today's data)
select count(*) as combined_orders
from HGI.GOLD.FCT_ORDERS
where created_at >= '2026-04-01' and created_at < '2026-05-01';

-- Per-brand breakdown for April 2026
select store_id, count(*) as orders
from HGI.GOLD.FCT_ORDERS
where created_at >= '2026-04-01' and created_at < '2026-05-01'
group by 1
order by 1;

-- March 2026 (for filter-change validation, capture into the Basecamp comment)
select count(*) as combined_orders
from HGI.GOLD.FCT_ORDERS
where created_at >= '2026-03-01' and created_at < '2026-04-01';
```

Expected April 2026 breakdown today: Revitalash ~2,637, iS Clinical ~29, Deese PRO 20, Geske 0. Combined ~2,686. PDF target 3,791 (incl HGI) / 3,764 (excl HGI).

## Post deploy ops (paste into the PR description)

> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_combined_shopify_orders.py` (step 7).

(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed

This ticket does not introduce any new sources, schemas, roles, or conventions. No `CLAUDE.md` updates are expected. If during the work you discover a drift (e.g. an additional Shopify store has been connected in the meantime, or the `order_count` metric has been renamed), fix `CLAUDE.md` in the same PR per the "Keeping this file current" section.
