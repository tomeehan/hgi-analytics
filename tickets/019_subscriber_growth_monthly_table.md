# 019: 12-month subscriber growth monthly table

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-019-subscriber_growth_monthly_table`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-019-subscriber_growth_monthly_table`.
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
- Page 18, section "iS Clinical, 12-month subscriber growth" (the monthly table is the lower block of the page, headed `MONTH / SUBSCRIBED / UNSUBSCRIBED / NET`; it starts on page 18 with the May 25 to Dec 25 rows and continues onto page 19 with the Jan 26 to Apr 26 rows plus the "12-month total" row). The section is sub-titled "Klaviyo (Subscribed / Unsubscribed events, May 2025 to Apr 2026)".
- April 2026 value (iS Clinical): the April 26 row reads `+624` subscribed, `-348` unsubscribed, **`+276`** net. The full trailing 12-month table (May 2025 to April 2026) is:

  | Month | Subscribed | Unsubscribed | Net |
  |---|---|---|---|
  | May 25 | +491 | -185 | **+306** |
  | Jun 25 | +478 | -180 | **+298** |
  | Jul 25 | +392 | -390 | **+2** |
  | Aug 25 | +378 | -940 | **-562** |
  | Sep 25 | +355 | -943 | **-588** |
  | Oct 25 | +405 | -323 | **+82** |
  | Nov 25 | +3,390 | -685 | **+2,705** |
  | Dec 25 | +243 | -528 | **-285** |
  | Jan 26 | +338 | -291 | **+47** |
  | Feb 26 | +328 | -631 | **-303** |
  | Mar 26 | +637 | -330 | **+307** |
  | Apr 26 | +624 | -348 | **+276** |
  | **12-month total** | **+8,059** | **-5,774** | **+2,285** |

  This table is the tabular counterpart of the totals KPI strip on ticket 017 and the monthly bar chart on ticket 018. All three read the same numbers; this ticket reproduces them as a 12-row table.

## Metric definition
- Per-month subscriber growth for iS Clinical, shown as a table with one row per calendar month over the trailing 12 months. Each row carries three numbers: **subscribed** (count of Klaviyo "Subscribed to Email Marketing" events that month), **unsubscribed** (count of Klaviyo "Unsubscribed from Email Marketing" events that month), and **net** (subscribed minus unsubscribed). A positive net means the subscribed base grew that month; a negative net means it shrank.
- Source of truth chain per the PDF appendix: **Klaviyo**. The subscribe/unsubscribe events come from the iS Clinical Klaviyo account (`BRONZE_KLAVIYO_ISCLINICAL.EVENTS`), identified by their Klaviyo metric name resolved via `BRONZE_KLAVIYO_ISCLINICAL.METRICS`.
- Filter behaviour: this tile is a 12-month rolling table, **not** a single-month metric. It always shows the trailing 12 months ending at the report's reference month. See the "Lightdash work" section for exactly how it relates to the dashboard's Month filter (the dashboard Month filter must not collapse it to a single row).

## Data dependencies
- Bronze sources needed: `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` (the Klaviyo subscribe/unsubscribe events) and `BRONZE_KLAVIYO_ISCLINICAL.METRICS` (the Klaviyo metric catalogue, used to resolve `metric_id` to a human-readable metric name like "Subscribed to Email Marketing"). Status from generator section (c): **iS Clinical Klaviyo is Live.** No Shopify dependency, so the iS Clinical Shopify sync gap does not apply to this ticket.
- Silver models that already cover this (verified against the repo): `dbt/models/silver/stg_klaviyo__events.sql` exists and unions iS Clinical and Deese PRO Klaviyo events, exposing `event_id`, `event_type`, `occurred_at`, `value`, `value_currency`, `unique_id`, `campaign_id`, `flow_id`, `message_id`, `profile_id`, `metric_id`, `store_id`. `dbt/models/silver/stg_klaviyo__metrics.sql` exists and exposes the Klaviyo metric catalogue with columns `metric_id`, **`metric_name`**, `integration_name`, `store_id`. Join `stg_klaviyo__events` to `stg_klaviyo__metrics` on `metric_id` to resolve the metric name. Note the metric-name column is named `metric_name` (not `name`). Both Silver models already exist; **no Silver changes are required.**
- Gold models that already cover this (verified against `dbt/models/gold/`): **none.** There is no Gold subscriber-growth model today. `dbt/models/gold/` contains Klaviyo models `fct_klaviyo_revenue.sql` (placed-order revenue, has `order_month`) and `fct_campaign_performance.sql` (campaign-level stats, has a campaign-level `unsubscribed` column and a `send_month`), but neither aggregates subscribe/unsubscribe **events** at a monthly grain. Do not pretend a Gold subscriber model exists.
- New Gold model required: a `fct_klaviyo_subscriber_growth` monthly fact (one row per `store_id` per month). This is the "dbt work" below. **This model is shared with tickets 017 (12-month subscriber growth totals) and 018 (12-month subscriber growth monthly bar chart).** Whichever of 017, 018, 019 runs first builds the model; the later two reuse it and add no new dbt work. Do not build a second model for the same data.

## dbt work
- **If `fct_klaviyo_subscriber_growth` does not yet exist (tickets 017, 018, 019 share it):** create `dbt/models/gold/fct_klaviyo_subscriber_growth.sql`.
  - Read from `stg_klaviyo__events` joined to `stg_klaviyo__metrics` on `metric_id` to resolve the metric name. Filter to the two subscribe/unsubscribe metrics (match on the Klaviyo metric name: "Subscribed to Email Marketing" and "Unsubscribed from Email Marketing"; confirm the exact strings with the Snowflake fallback SQL, Klaviyo metric naming can vary).
  - Grain: one row per `store_id` per month. Columns: `store_id`, `order_month` (`date_trunc('month', occurred_at)::date`, named `order_month` so the dashboard Month filter can cross-apply, see generator section (d)), `subscribed_count`, `unsubscribed_count`, `net_subscribers` (`subscribed_count - unsubscribed_count`).
  - Compute the counts with conditional aggregation: `count_if(metric_name = 'Subscribed to Email Marketing') as subscribed_count`, `count_if(metric_name = 'Unsubscribed from Email Marketing') as unsubscribed_count`, grouped by `store_id` and the month.
  - Add a surrogate key `subscriber_growth_id` (e.g. `{{ dbt_utils.generate_surrogate_key(['store_id', 'order_month']) }}`) so the model has a clean unique key.
  - Add the model to `dbt/models/gold/_schema.yml` with: `not_null` and `unique` on `subscriber_growth_id`; `not_null` on `store_id` and `order_month`; a `dbt_utils.accepted_range` test asserting `subscribed_count >= 0` and `unsubscribed_count >= 0`.
  - After creating the model, `cd dbt && dbt build --select fct_klaviyo_subscriber_growth+` and confirm tests pass.
- **If `fct_klaviyo_subscriber_growth` already exists (ticket 017 or 018 built it first):** write "no dbt changes needed" and proceed straight to the Lightdash work. The table in this ticket needs only `order_month`, `subscribed_count`, `unsubscribed_count`, `net_subscribers`, all of which the shared model already exposes. No extra column is required for the table tile.

## Lightdash work
- **Tile type:** table. The PDF block is a literal 12-row table (`MONTH / SUBSCRIBED / UNSUBSCRIBED / NET`), so this tile is a Lightdash table chart, not a big number or bar.
- **Placement:** on the iS Clinical KPI Report dashboard, in the subscriber-growth block that mirrors PDF pages 18 to 19. It sits directly below the 12-month subscriber growth monthly bar chart (ticket 018), reproducing the PDF page order: totals strip (ticket 017), then the monthly bar chart (ticket 018), then this monthly table.
- **Chart YAML:** check `lightdash/charts/` first for an existing subscriber-growth chart to adapt. Tickets 017 and 018 may already have created `lightdash/charts/` files against the shared `fct_klaviyo_subscriber_growth` explore (for example a totals chart or `subscriber-growth-monthly-bar-chart.yml`); reuse the explore but this tile needs its own table chart, so create `lightdash/charts/subscriber-growth-monthly-table.yml`. It charts the `fct_klaviyo_subscriber_growth` explore as `chartType: table`, with dimension `order_month` and metrics `subscribed_count`, `unsubscribed_count`, `net_subscribers` (sum metrics on the columns), sorted by `order_month` ascending so the rows read May 25 at the top to Apr 26 at the bottom, matching the PDF. Show column totals if the live Lightdash table config supports it, so the table footer reproduces the PDF's "12-month total" row (`+8,059 / -5,774 / +2,285`).
- **Dashboard YAML:** update `lightdash/dashboards/kpi-report.yml` to add the table tile in the subscriber-growth block, below the ticket 018 bar-chart tile.
- **Mandatory Source comment:** every chart and dashboard YAML file you create or edit must have, as its very first line, the exact comment `# Source: April 2026 KPI Report, page 18 (iS Clinical, 12-month subscriber growth)`.
- **Month filter relationship (important, this is a rolling 12-month table, not a single-month metric):** the dashboard Month filter is a single-month filter (`fct_orders_order_month_label` on the `fct_orders` explore, default `2026-04`). This tile must **not** collapse to a single row when the Month filter is set, it must always show 12 monthly rows. Two acceptable approaches, pick whichever the live YAML supports cleanly:
  1. **Exclude this tile from the Month filter** by not adding a `tileTargets` entry for it (or pointing its target at no field), so the dashboard Month filter does not cross-apply. The table then shows all months in `fct_klaviyo_subscriber_growth`, and a chart-level "last 12 months" date filter (on `order_month`) keeps it to a trailing year.
  2. **Cross-apply as a rolling window** if the live Lightdash version supports a relative / "in the last 12 months" filter target, so the Month filter shifts the 12-month window rather than slicing to one row.
  Approach 1 is the simpler and recommended default, and is consistent with how ticket 018's bar chart handles the same Month filter. Either way, confirm the underlying `fct_klaviyo_subscriber_growth` explore exposes `order_month` (the model creates it as `date_trunc('month', occurred_at)::date`) so it is consistent with the rest of the dashboard, and document in the YAML / PR which approach was taken and why the tile is intentionally not month-scoped.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table. Because this is a rolling 12-month table, the Month filter should not collapse it: confirm the table still shows 12 monthly rows.
- Assert the rows match the PDF table in the "PDF reference" section above, in particular: the Apr 26 row reads `+624` subscribed, `-348` unsubscribed, `+276` net; the Nov 25 row is the standout at `+3,390 / -685 / +2,705`; Aug 25 and Sep 25 are the deepest negatives at `-562` and `-588` net. If the table footer shows column totals, assert they read `+8,059 / -5,774 / +2,285`.
- If it does not match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (wrong metric-name match, wrong month bucketing) or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`):
```sql
-- Step 1: confirm the exact Klaviyo metric names for subscribe / unsubscribe events.
select m.metric_name, count(*) as event_count
from hgi.silver.stg_klaviyo__events e
join hgi.silver.stg_klaviyo__metrics m
  on e.metric_id = m.metric_id
 and e.store_id = m.store_id
where e.store_id = 'isclinical'
  and lower(m.metric_name) like '%subscribed%email%'
group by 1
order by 2 desc;

-- Step 2: subscriber growth per month, trailing 12 months (May 2025 to Apr 2026).
-- Substitute the exact metric-name strings confirmed in step 1 if they differ.
select
    date_trunc('month', e.occurred_at)::date                    as order_month,
    count_if(m.metric_name = 'Subscribed to Email Marketing')      as subscribed_count,
    count_if(m.metric_name = 'Unsubscribed from Email Marketing')  as unsubscribed_count,
    subscribed_count - unsubscribed_count                          as net_subscribers
from hgi.silver.stg_klaviyo__events e
join hgi.silver.stg_klaviyo__metrics m
  on e.metric_id = m.metric_id
 and e.store_id = m.store_id
where e.store_id = 'isclinical'
  and m.metric_name in ('Subscribed to Email Marketing', 'Unsubscribed from Email Marketing')
  and e.occurred_at >= '2025-05-01'
  and e.occurred_at <  '2026-05-01'
group by 1
order by 1;
-- Expected April 2026 row: 624 subscribed, 348 unsubscribed, 276 net.
-- Expected 12-month totals: 8,059 subscribed, 5,774 unsubscribed, 2,285 net.
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). If this ticket is the one that creates `fct_klaviyo_subscriber_growth` (because it runs before tickets 017 and 018), that adds a new Gold model: if the `CLAUDE.md` Gold-layer model list enumerates fact tables, add the new model there in the same PR, and note that the model is shared by tickets 017, 018 and 019. If 017 or 018 already created the model, no `CLAUDE.md` change is needed for this ticket.
