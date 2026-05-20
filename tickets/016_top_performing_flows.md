# 016: Top performing Klaviyo flows

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-016-top_performing_flows`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-016-top_performing_flows`.
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
- Page 16, section "IS CLINICAL, 7. CRM Performance" (the "TOP PERFORMING FLOWS" table, lower-right of the page; the page header reads "KLAVIYO (PLACED ORDER, 5-DAY WINDOW)").
- April 2026 value (iS Clinical): the top 5 Klaviyo automated flows ranked by attributed revenue:

  | Flow | Revenue |
  |---|---|
  | Welcome Series (NEW) | £5,277 |
  | Abandoned Checkout | £2,642 |
  | Abandoned Cart | £2,582 |
  | Abandoned Checkout (variant) | £1,124 |
  | Abandoned Cart (variant) | £667 |

  These five flows sum to £14,292, which is the same order of magnitude as the page's "FLOW REV" headline of £14,218 (the headline counts all flows, the table shows only the top 5).

## Metric definition
- The top iS Clinical Klaviyo automated flows for the month, ranked by the revenue Klaviyo attributes to each flow. A "flow" is a Klaviyo automation (Welcome Series, Abandoned Checkout, Abandoned Cart, etc.) as opposed to a one-off campaign send. Revenue per flow is the sum of order value across Klaviyo "Placed Order" events attributed to that `flow_id` within Klaviyo's 5-day attribution window.
- Source of truth chain per the PDF appendix: **Klaviyo** (Placed Order events, flow-attributed, 5-day window). Not Shopify, GA4, Meta or Google Ads. This is the flow-side companion of ticket 015 (top performing campaigns) and the flow-attributed half of ticket 014's CRM KPI strip (flow rev £14,218).
- Filter behaviour: the tile is a table scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the table must show the five flows above, ordered by revenue descending, limited to the top 5.

## Data dependencies
- Bronze source needed: `BRONZE_KLAVIYO_ISCLINICAL`, status **Live** per generator section (c). No Shopify sync-gap note applies (this is a Klaviyo-sourced tile, not a Shopify-sourced one).
- The raw data is fully present, this tile is buildable now. `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` holds 5.9M rows all-time (April 2026 includes 2,092 Placed Order events plus rich Received / Opened / Clicked Email engagement events), and `BRONZE_KLAVIYO_ISCLINICAL.FLOWS` holds 45 rows mapping flow id to flow name. The only empty things are the dbt Gold models (not yet built) and Klaviyo's pre-aggregated reporting streams (`CAMPAIGN_VALUES_REPORTS`, `FLOW_SERIES_REPORTS`), which are deliberately not synced by Airbyte's lean stream selection. This is a modelling gap, not a data gap: flow revenue is computed off raw `EVENTS`.
- Relevant Bronze structure:
  - `EVENTS.RELATIONSHIPS:metric:data:id` joins to `METRICS.ID`; the metric name is `METRICS.ATTRIBUTES:name`. The event payload is in `EVENTS.ATTRIBUTES:event_properties`, and `EVENTS.DATETIME` is the timestamp.
  - Engagement events (Received / Opened / Clicked Email) carry `$message`, `$flow` (the flow id), `$campaign` and `Campaign Name` in `event_properties`. Placed Order events carry `$value` and `$currency_code` but **no** `$flow` or `$campaign`, so flow revenue is an attribution computation.
  - `FLOWS` supplies the human-readable flow name per flow id, so a flow dimension is buildable today.
- Silver and Gold models that already cover this: there are no Klaviyo flow-revenue models in the repo yet. The Silver staging and Gold fact described under "dbt work" are new and built off raw `EVENTS` and `FLOWS`.

## dbt work
- **Add a Silver flow dimension, `dbt/models/silver/stg_klaviyo__flows.sql`.** Klaviyo exposes flows on the `flows` stream, already syncing into `BRONZE_KLAVIYO_ISCLINICAL.FLOWS` (45 rows, one per flow, with `id` and `attributes:name`). Add a `bronze_klaviyo_isclinical.flows` source to `dbt/models/bronze/_sources.yml` if it is not already declared, then build a staging model `stg_klaviyo__flows` with columns `flow_id`, `flow_name`, `store_id`, following the multi-brand CTE-per-account union convention in `CLAUDE.md`.
- **Add a Silver attribution staging model, `dbt/models/silver/stg_klaviyo__flow_attribution.sql`** (or fold this logic into a shared Klaviyo attribution staging model alongside ticket 015). Build it off raw `EVENTS`:
  - Join `EVENTS` to `METRICS` on `RELATIONSHIPS:metric:data:id = METRICS.ID` to resolve metric names.
  - Take flow-email engagement events (Received / Opened / Clicked Email rows that carry a `$flow`) as the attribution source, and Placed Order events (carrying `$value`) as the revenue source.
  - For each Placed Order event, attribute its `$value` to the `$flow` of the same profile's most recent flow-email engagement within a 5-day window before the order. Emit `flow_id`, `revenue`, `order_month`, `store_id` per attributed order.
- **Add a Gold model `dbt/models/gold/fct_klaviyo_flow_revenue.sql`.** Grain: one row per flow per month. It joins the flow-attribution staging model to `stg_klaviyo__flows` on `flow_id` + `store_id`, and aggregates `sum(revenue) as flow_revenue` grouped by `flow_id`, `flow_name`, `store_id`, `order_month`. Expose a `flow_revenue` metric (`type: sum`, `format: gbp`) and the `order_month` / `order_month_label` dimensions so the dashboard Month filter applies.
- Tests to add (in `dbt/models/gold/_schema.yml` and `dbt/models/silver/_schema.yml`):
  - `stg_klaviyo__flows`: `not_null` + `unique` on `flow_id`, `not_null` on `store_id`.
  - `fct_klaviyo_flow_revenue`: `not_null` on `flow_id`, `flow_name`, `store_id`, `order_month`; `dbt_utils.unique_combination_of_columns` on (`flow_id`, `order_month`, `store_id`); a `dbt_utils.accepted_range` (`min_value: 0`) range test on `flow_revenue`.
- Run `cd dbt && dbt build --select stg_klaviyo__flows+ fct_klaviyo_flow_revenue+` and confirm tests pass.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard in the row that mirrors the PDF page 16 (CRM Performance) layout, in the lower-right position. It is the flow-side companion of ticket 015's "Top performing campaigns" table (lower-left of the same PDF page): place this tile immediately after the ticket 015 campaigns table, and after the ticket 014 CRM KPI strip.
- Create `lightdash/charts/isclinical-top-flows.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing chart that already fits and adapt it instead. The ticket 015 "top campaigns" table chart (once it exists) is the closest template: a table on a Klaviyo revenue-by-attribution-unit explore, sorted by revenue descending with a row limit of 5. Adapt that rather than writing from scratch.
  - The chart is a table on the `fct_klaviyo_flow_revenue` explore, with `flow_name` as the dimension and `flow_revenue` as the metric, sorted by `flow_revenue` descending, row limit 5. Set `flipAxes` is not relevant for a table tile; this is a plain two-column table (Flow, Revenue), matching the PDF.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 16 (IS CLINICAL, 7. CRM Performance)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. `fct_klaviyo_flow_revenue` must expose a matching `order_month_label` dimension (`to_char(order_month, 'YYYY-MM')`) so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_klaviyo_flow_revenue_order_month_label` via `tileTargets` in `kpi-report.yml`. Confirm `order_month_label` is present on the `fct_klaviyo_flow_revenue` explore before editing the YAML, this is a hard requirement from generator section (d).

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert it shows the five flows from the "PDF reference" section above, in revenue-descending order: Welcome Series (NEW) £5,277, Abandoned Checkout £2,642, Abandoned Cart £2,582, Abandoned Checkout (variant) £1,124, Abandoned Cart (variant) £667.
- If it does not match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (an attribution-window edge case, a join key mismatch, a flow-name lookup miss). The 5-day window is an attribution heuristic, so small per-flow deltas against the PDF are expected, the ranking and the rough magnitudes should hold.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`):
```sql
select flow_name, sum(flow_revenue) as revenue
from HGI.GOLD.FCT_KLAVIYO_FLOW_REVENUE
where store_id = 'isclinical'
  and order_month = '2026-04-01'
group by flow_name
order by revenue desc
limit 5;
```
Expected per the PDF: Welcome Series (NEW) `5277`, Abandoned Checkout `2642`, Abandoned Cart `2582`, Abandoned Checkout (variant) `1124`, Abandoned Cart (variant) `667`. To sanity-check the source data directly off raw `EVENTS`, confirm the Placed Order and engagement events and the flow lookup are all present for April 2026:
```sql
select m.attributes:name::string as metric_name, count(*) as events
from HGI.BRONZE_KLAVIYO_ISCLINICAL.EVENTS e
join HGI.BRONZE_KLAVIYO_ISCLINICAL.METRICS m
  on e.relationships:metric:data:id::string = m.id
where date_trunc('month', e.datetime) = '2026-04-01'
group by metric_name
order by events desc;
```
This should show a healthy Placed Order count (~2,092) alongside Received / Opened / Clicked Email engagement events. Also confirm the `FLOWS` lookup is populated:
```sql
select count(*) as flow_rows
from HGI.BRONZE_KLAVIYO_ISCLINICAL.FLOWS;
```
This returns 45, supplying the flow-id-to-flow-name mapping for `stg_klaviyo__flows`.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds a new `flows` Bronze source and the `stg_klaviyo__flows`, `stg_klaviyo__flow_attribution` and `fct_klaviyo_flow_revenue` models, so update the Gold-layer model list and the Klaviyo source notes in `CLAUDE.md` accordingly.
