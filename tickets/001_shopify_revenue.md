# 001: iS Clinical Shopify Revenue

> **Project (one paragraph):** This repo is `hgi-analytics`. We ingest Shopify, Klaviyo, Meta, GA4, Google Ads, Cin7 and Prospect CRM into Snowflake via Airbyte, transform with dbt (Bronze, Silver, Gold), and serve dashboards from Lightdash. Full project README is `CLAUDE.md` in the repo root. Read it first if you have not seen this project before. Lightdash charts and dashboards are managed as code (YAML in `lightdash/charts/` and `lightdash/dashboards/`); read the "Lightdash dashboards-as-code" section of `CLAUDE.md` before touching any tile.
>
> **Wider goal of these tickets:** Build the **iS Clinical KPI Report** dashboard in Lightdash, the iS Clinical version of the April 2026 KPI Report PDF (`reference/april_2026_kpi_report.pdf`). The PDF is treated as numerically authoritative. Each ticket builds one tile on the **iS Clinical KPI Report** dashboard and verifies the April 2026 iS Clinical number against the PDF. This is a single-brand dashboard: there is no Brand filter, only a Month filter.
>
> **The generator that produced this ticket:** `tickets/_ticket_generator.md`. Read sections (c) data availability map and (d) filter design before starting if you have not touched these tickets before.
>
> **Context window discipline:** Spawn subagents (Explore for codebase searches, Plan for design questions, general purpose for multi step research) so this session's context stays focused on the implementation. Do not foreground read every file linked from this ticket. Delegate.
>
> **This ticket is fully autonomous.** You are responsible for taking the work from Triage all the way to merged, deployed and verified. Do not stop for human approval at any intermediate step. The end state is: PR merged to main, `lightdash_deploy.yml` green on main (it auto-runs `lightdash deploy` then `lightdash upload --force`), the dashboard tile verified against the PDF number, and the Basecamp card moved to Done with a verification comment.

## End to end workflow (run this top to bottom, autonomously)

1. **Claim the card on Basecamp.** Using the `basecamp` skill, find this ticket on the Data Engineering card table (account `5735756`, bucket `46863097`, card table `9778948512`), and move it from **Triage** to **In progress**.
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-001-shopify_revenue`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement dbt changes (if any).** Edit the models listed in the "dbt work" section, then run `cd dbt && dbt build --select <model>+` and confirm tests pass. If there are no dbt changes, skip this step.
4. **Edit the Lightdash YAML.**
   - Run `lightdash download` from the repo root to refresh the local `lightdash/charts/` and `lightdash/dashboards/` YAML from production, so you start editing from live state.
   - Before creating a new chart YAML, check `lightdash/charts/` for an existing chart that already fits this tile and adapt it instead of writing a new one.
   - Edit or create `lightdash/charts/<slug>.yml` (one file per tile) and update `lightdash/dashboards/kpi-report.yml` to add the tile.
   - Every chart and dashboard YAML file you create or edit **must** carry, as the very first line, a comment in the exact form `# Source: April 2026 KPI Report, page <N> (<section title>)`.
   - `lightdash lint` to validate the YAML against Lightdash's JSON schema. Optionally `lightdash run-chart lightdash/charts/<slug>.yml` to confirm the query runs against the warehouse.
5. **Preview the change.**
   - Create a preview project and push the YAML into it:
     ```sh
     lightdash start-preview --name "$(git branch --show-current)" \
       --project-dir dbt --profiles-dir dbt
     lightdash upload --force --validate --project <preview-uuid>
     ```
   - Open the printed preview URL, confirm the new tile renders on the iS Clinical KPI Report dashboard, and confirm the April 2026 value matches the PDF (see the "Preview verification" section).
6. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-001-shopify_revenue`.
   - `gh pr create`. The PR body notes that `lightdash_deploy.yml` runs automatically on merge (it deploys the semantic layer and uploads the chart/dashboard YAML); there is no manual post-deploy step.
7. **Self merge on green CI.**
   - `gh pr checks <pr-number> --watch` until CI is green.
   - `gh pr merge --rebase --delete-branch`. Never push to main directly. Never use `--no-verify` or skip hooks.
8. **Watch the deploy.**
   - On merge, `lightdash_deploy.yml` runs automatically (it runs `lightdash deploy` then `lightdash upload --force`, pushing the committed YAML to the production project). Poll with `gh run list --workflow=lightdash_deploy.yml --limit 1 --json status,conclusion,databaseId --jq '.[0]'`, or `gh run watch <run-id>`. Wait until `status=completed, conclusion=success`.
9. **Verify the production tile.** Open the iS Clinical KPI Report dashboard in Lightdash, with the Month filter on April 2026, and confirm the tile value matches the PDF number for this metric.
10. **Tear down the preview.** `lightdash stop-preview --name "<branch-name>"`.
11. **Close the loop on Basecamp.** Add a comment to the card with the merged PR URL, the verified April value, and any caveats or known gaps (especially if the live number does not match the PDF, link the prerequisite ticket). Move the card from **In progress** to **Done**.
12. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page 12, section "Revenue & Channel Attribution" (iS Clinical brand section, KPI strip, "Total Revenue (Shopify)").
- April 2026 value (iS Clinical): **£144,532** (the PDF labels it "1,075 orders, source of truth").

## Metric definition
- Total gross Shopify revenue for the iS Clinical store in a calendar month: the sum of every order's `total_price` (order value in the order's currency, before refunds are netted off).
- Source of truth chain per the PDF appendix: Shopify is the source of truth for revenue. The PDF strip explicitly tags this figure "Shopify (source of truth)" and contrasts it with the GA4 channel-attributed revenue (£73,808) shown alongside it. This tile reproduces the Shopify figure only.
- Filter behaviour: the tile is a single big number that responds to the dashboard's **Month** filter. With the Month filter on April 2026 it reads the April total; changing the month re-scopes it.

## Data dependencies
- Bronze source needed: `BRONZE_SHOPIFY_ISCLINICAL` (Shopify orders for the iS Clinical store).
- **Known data gap (iS Clinical Shopify Airbyte sync is degraded).** The iS Clinical Shopify source authenticates with a rotating OAuth token (not a static custom-app token). The token fails mid-sync, and when it does Airbyte silently drops scattered records rather than erroring loudly. Bronze runs roughly **2.6% short** per month. For April 2026, Bronze holds **1,047 orders** against the **1,075** stated in the PDF, so the live revenue tile will read slightly **below** the £144,532 PDF figure. The PDF figure is authoritative. A separate data-engineering ticket should fix the rotating OAuth token (`fix iS Clinical Shopify sync`); this ticket links it as a prerequisite. If that ticket does not exist yet, create it on the Data Engineering board (Triage) describing the rotating-token failure mode before closing this card. Note the gap in the Basecamp verification comment.
- Silver and Gold models that already cover this: `dbt/models/silver/stg_shopify__orders.sql` (Silver staging, unioned across stores, carries `store_id`) and `dbt/models/gold/fct_orders.sql` (Gold fact, one row per order, adds `order_month` and `is_first_order`).
- New Silver or Gold models or columns required: none. `fct_orders` already exposes a `total_revenue` metric (`sum` of `total_price`, `gbp` format) and the `order_month` / `order_month_label` dimensions in `dbt/models/gold/_schema.yml`.

## dbt work
- No dbt changes needed. `dbt/models/gold/fct_orders.sql` and its schema entry in `dbt/models/gold/_schema.yml` already provide everything: the `total_revenue` metric on `total_price`, plus the `order_month` date dimension and the `order_month_label` additional dimension (`YYYY-MM` string) that the dashboard Month filter targets.
- Tests: `fct_orders` already has `not_null` and `unique` on `order_id`. No new tests required for this tile.

## Lightdash work
- Tile type: **big number**. It sits at the top of the iS Clinical KPI Report dashboard, in the first row (under the "Revenue & Channel Attribution" heading from PDF page 12), as the first KPI of the report. Tickets 002 to 020 append their tiles below it in PDF reading order.
- Chart YAML: create or adapt `lightdash/charts/isclinical-shopify-revenue.yml` (one file per tile). The dashboard already carries a `Combined Shopify Revenue` chart (`combined-shopify-revenue`) which is a cross-brand chart being removed by this ticket (see the dashboard rescope below); check `lightdash/charts/` for it and either adapt a copy or write a fresh single-brand chart. The chart is a big-number on the `fct_orders` explore, selecting the `total_revenue` metric, filtered to `store_id = isclinical` so the single-brand dashboard always shows the iS Clinical figure regardless of the (now removed) Brand filter.
- **Dashboard rescope (this ticket only).** Edit `lightdash/dashboards/kpi-report.yml`:
  - rename the dashboard from "KPI Report" to **"iS Clinical KPI Report"** (the `name` field),
  - **drop the disabled Brand filter** entirely: the `fct_orders_store_id` dimension filter block under `filters.dimensions` (the one with `disabled: true`, `label: Brand`),
  - **remove the four cross-brand tiles**: `per-brand-breakdown`, `meta-spend-share-by-brand`, `ga4-revenue-share-by-brand`, and `april-at-a-glance` (delete their tile entries from `tiles`),
  - **keep the Month filter** on `fct_orders_order_month_label`, operator `equals`, default value `2026-04`,
  - add the new iS Clinical Shopify Revenue big-number tile as the first tile.
  Tickets 002 to 020 each append exactly one further tile to this rescoped dashboard. After this ticket the dashboard's only filter is Month.
- Mandatory: every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 12 (Revenue & Channel Attribution)`. This applies to both `lightdash/charts/isclinical-shopify-revenue.yml` and `lightdash/dashboards/kpi-report.yml`.
- Before creating a new chart YAML, check `lightdash/charts/` for an existing chart that already fits and adapt it instead.
- How the tile picks up the dashboard's Month filter: the `fct_orders` explore exposes `order_month` (a `date` dimension) and the `order_month_label` additional dimension (a `YYYY-MM` string), confirmed in `dbt/models/gold/_schema.yml`. The dashboard Month filter targets `fct_orders_order_month_label`. Because this tile reads from `fct_orders` directly, the filter applies without any `tileTargets` cross-apply. Confirm `order_month_label` is still present before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile value.
- Assert it equals the April 2026 iS Clinical value stated in the "PDF reference" section above (**£144,532**).
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or the known iS Clinical Shopify sync gap from section (c), and note the cause in the ticket. A tile reading a few percent low (around £140k against £144,532) is the expected symptom of the degraded sync, not a model bug: in that case verify the order count is close to the 1,047 ingested figure, note it as the known gap, link the `fix iS Clinical Shopify sync` prerequisite, and proceed.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
select
    count(distinct order_id)        as orders,
    round(sum(total_price), 0)      as total_revenue
from hgi.gold.fct_orders
where store_id = 'isclinical'
  and order_month = date '2026-04-01';
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). At minimum, the dashboard rename ("KPI Report" to "iS Clinical KPI Report") and the removal of the cross-brand tiles and Brand filter are conventions worth reflecting if `CLAUDE.md` references the old dashboard shape.
