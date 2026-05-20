# 004: iS Clinical Klaviyo Revenue

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-004-klaviyo_revenue`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-004-klaviyo_revenue`.
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
- Page 16, section "IS CLINICAL, 7. CRM Performance".
- April 2026 value (iS Clinical): **£64,885**.

The PDF cover page shows a *combined* (cross-brand) Klaviyo revenue figure. This ticket uses the **iS Clinical-only** figure, taken from the "TOTAL CRM REVENUE" headline on the iS Clinical CRM Performance page (page 16), measured as Klaviyo Placed Order revenue on a 5-day attribution window. On that page the headline decomposes into Campaign Rev £50,667 (78.1%) and Flow Rev £14,218 (21.9%), which sum to £64,885.

## Metric definition
- Total revenue Klaviyo claims credit for: the sum of order value across Klaviyo "Placed Order" events that are attributed to either a campaign or a flow within Klaviyo's 5-day attribution window, for iS Clinical.
- Source of truth chain per the PDF appendix: **Klaviyo** (Placed Order events, campaign-attributed and flow-attributed, 5-day window). Not Shopify, GA4, Meta or Google Ads.
- Filter behaviour: the tile is a big number scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the tile must read £64,885 (the PDF's iS Clinical figure).

## Data dependencies
- Bronze source needed: `BRONZE_KLAVIYO_ISCLINICAL`, status **Live** per generator section (c). No Shopify sync-gap note applies (this is a Klaviyo-sourced tile, not a Shopify-sourced one).
- The Klaviyo data is fully present. `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` holds 5.9M rows all-time. April 2026 alone: Received Email 111,146, Opened Email 104,230, Clicked Email 3,426, Placed Order 2,092. This tile is buildable now off the raw events; there is no upstream blocker and no prerequisite ticket.
- This is a modelling gap, not a data gap. The only empty things are the legacy dbt Gold model `dbt/models/gold/fct_klaviyo_revenue.sql` (0 rows) and Klaviyo's pre-aggregated reporting streams in Bronze (`CAMPAIGN_VALUES_REPORTS`, `FLOW_SERIES_REPORTS`, both 0 rows, deliberately not synced by Airbyte's lean stream selection). The raw `EVENTS` data is not missing.
- `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` structure: `EVENTS.RELATIONSHIPS:metric:data:id` joins to `METRICS.ID`; the metric name is `METRICS.ATTRIBUTES:name`. The event payload is in `EVENTS.ATTRIBUTES:event_properties` and `EVENTS.DATETIME` is the timestamp. Engagement events (Received, Opened, Clicked Email) carry `$message`, `$campaign`, `$flow` and `Campaign Name` in `event_properties`. Placed Order events carry `$value` (order revenue) and `$currency_code` but no `$campaign` / `$flow` / `$message`.
- New Silver and Gold models required (see "dbt work"): a Silver staging model over `EVENTS` and a rebuilt Gold `fct_klaviyo_revenue` that computes the 5-day-window attribution from raw events. The tile's `total_klaviyo_revenue` metric and `order_month` / `order_month_label` dimensions land on the rebuilt Gold model.

## dbt work
Build the Gold model from the raw `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` table. The legacy `fct_klaviyo_revenue` is empty because it depended on Klaviyo's pre-aggregated reporting streams, which are deliberately not synced; rebuild it off raw events instead.

- **New Silver staging model**, `dbt/models/silver/stg_klaviyo__events.sql` (or similar). One row per Klaviyo event. Select from `BRONZE_KLAVIYO_ISCLINICAL.EVENTS`, join `RELATIONSHIPS:metric:data:id` to `METRICS.ID` to resolve the metric name from `METRICS.ATTRIBUTES:name`, and extract: the profile id, the metric name, `EVENTS.DATETIME` as the event timestamp, the engagement keys (`$campaign`, `$flow`, `$message`, `Campaign Name`) from `event_properties` for engagement events, and `$value` / `$currency_code` from `event_properties` for Placed Order events. Add `store_id = 'isclinical'` and `date_trunc('month', datetime) as order_month`.
- **Rebuild the Gold model** `dbt/models/gold/fct_klaviyo_revenue.sql`. Grain: one row per attributed Placed Order event. For each Placed Order event, find the same profile's most recent qualifying email engagement (Received / Opened / Clicked Email) within the 5-day window before the order, and attribute the order's `$value` to that engagement's campaign or flow (matching the PDF's "Placed Order, 5-day window"). Carry `revenue`, `attribution_kind` (`campaign` or `flow`), `order_month`, `order_month_label` (`to_char(order_month, 'YYYY-MM')`) and `store_id`. Keep the `total_klaviyo_revenue` metric (`type: sum`, `format: gbp`) on this model.
- **Tests:** `not_null` + `unique` on `event_id`, `not_null` on `store_id` and `order_month`, and a `dbt_utils.accepted_range` (`min_value: 0`) range test on `revenue` (declare in `dbt/models/gold/_schema.yml` and the new Silver model's schema).

## Lightdash work
- Tile type: **big number**. It sits on the iS Clinical KPI Report dashboard in the row that mirrors the PDF's headline KPIs, alongside the other iSC headline big numbers built by tickets 001 to 003 (Shopify Revenue, Shopify Orders, Meta Spend). Place this one after `003: iS Clinical Meta Spend`.
- Create `lightdash/charts/isclinical-klaviyo-revenue.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing chart that already fits and adapt it instead. `combined-meta-spend.yml` and `combined-shopify-revenue.yml` are good big-number templates to adapt; there is no existing Klaviyo-revenue chart.
  - The chart is a big number on the `fct_klaviyo_revenue` explore, selecting the `total_klaviyo_revenue` metric.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 16 (IS CLINICAL, 7. CRM Performance)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. `fct_klaviyo_revenue` exposes a matching `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`), so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_klaviyo_revenue_order_month_label` via `tileTargets` in `kpi-report.yml`. Confirm `order_month_label` is present on the `fct_klaviyo_revenue` explore before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile value.
- Assert it equals the April 2026 iS Clinical value stated in the "PDF reference" section above (`£64,885`).
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below, and check the rebuilt `fct_klaviyo_revenue` against the raw `EVENTS` data to find out whether the gap is in the staging extraction or the 5-day-window attribution logic. A small gap is expected if a few Placed Orders fall outside the 5-day window of any email engagement (those orders are unattributed and excluded). Tune the attribution join until the April total lands on the PDF figure, then note the cause of any residual gap in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the Placed Order revenue directly from the raw Klaviyo events (via `snow sql -c hgi`). This sums every April 2026 iS Clinical Placed Order's `$value`, the universe the 5-day attribution draws from:
```sql
select
  count(*)                                              as placed_orders,
  sum(e.attributes:event_properties:"$value"::float)    as total_value
from HGI.BRONZE_KLAVIYO_ISCLINICAL.EVENTS    e
join HGI.BRONZE_KLAVIYO_ISCLINICAL.METRICS   m
  on e.relationships:metric:data:id::string = m.id::string
where m.attributes:name::string = 'Placed Order'
  and date_trunc('month', e.datetime) = '2026-04-01';
```
This total is the full Placed Order revenue before attribution; the rebuilt `fct_klaviyo_revenue` figure is this same revenue restricted to orders attributable to a campaign or flow within the 5-day window, and should land on the PDF's `£64,885`. Once the Gold model is built, also check it directly:
```sql
select attribution_kind, count(*) as events, sum(revenue) as revenue
from HGI.GOLD.FCT_KLAVIYO_REVENUE
where store_id = 'isclinical'
  and order_month = '2026-04-01'
group by attribution_kind
order by attribution_kind;
```
The `campaign` and `flow` rows should sum to `£64,885`, decomposing to roughly Campaign Rev `£50,667` and Flow Rev `£14,218` per the PDF.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket establishes the pattern of building Klaviyo CRM metrics from raw `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` with a 5-day-window attribution of Placed Order `$value` to campaign or flow; if that becomes a reusable convention across the Klaviyo tickets (`014` to `019`), record it in `CLAUDE.md`.
