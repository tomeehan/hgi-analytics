# 018: 12-month subscriber growth monthly bar chart

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-018-subscriber_growth_monthly_bar_chart`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-018-subscriber_growth_monthly_bar_chart`.
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
- Page 18, section "iS Clinical, 12-month subscriber growth" (the chart is sub-titled "Klaviyo (Subscribed / Unsubscribed events, May 2025 to Apr 2026)"; the section header reads "NET SUBSCRIBERS ADDED PER MONTH, green = growth, red = decline").
- April 2026 value (iS Clinical): the April bar is **+276** net subscribers (`+624` subscribed minus `-348` unsubscribed). The full trailing 12-month series of net values is:

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

  12-month totals: `+8,059` subscribed, `-5,774` unsubscribed, `+2,285` net. This chart is the visual counterpart of the totals on ticket 017 and the table on ticket 019.

## Metric definition
- Net subscribers added per calendar month for iS Clinical: the count of Klaviyo "Subscribed to Email Marketing" events minus the count of "Unsubscribed from Email Marketing" events, grouped by event month. A positive bar means the subscribed base grew that month; a negative bar means it shrank.
- Source of truth chain per the PDF appendix: **Klaviyo**. The subscribe/unsubscribe events come from the iS Clinical Klaviyo account (`BRONZE_KLAVIYO_ISCLINICAL.EVENTS`), identified by their Klaviyo metric name.
- Filter behaviour: this tile is a 12-month rolling trend, not a single-month metric. See the "Lightdash work" section for how it relates to the dashboard's Month filter. Each bar is one month of net subscriber change; the chart always shows the trailing 12 months ending at the report's reference month.

## Data dependencies
- Bronze sources needed: `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` (the Klaviyo subscribe/unsubscribe events) and `BRONZE_KLAVIYO_ISCLINICAL.METRICS` (the Klaviyo metric catalogue, used to resolve `metric_id` to a human-readable metric name like "Subscribed to Email Marketing"). Status from generator section (c): **iS Clinical Klaviyo is Live.** No Shopify dependency, so the iS Clinical Shopify sync gap does not apply to this ticket.
- Silver models that already cover this: `dbt/models/silver/stg_klaviyo__events.sql` unions iS Clinical and Deese PRO events and exposes `event_id`, `event_type`, `occurred_at`, `metric_id`, `profile_id`, `store_id`. `dbt/models/silver/stg_klaviyo__metrics.sql` exposes the Klaviyo metric catalogue (`metric_id`, metric name). Both already exist. **Verify** that `stg_klaviyo__metrics` exposes a metric-name column you can join on, and that the iS Clinical events table actually contains "Subscribed to Email Marketing" and "Unsubscribed from Email Marketing" metrics (the Snowflake fallback SQL below does this check).
- Gold models that already cover this: **none.** There is no Gold subscriber-growth model today. `dbt/models/gold/` has campaign and revenue Klaviyo models (`fct_campaign_performance`, `fct_klaviyo_revenue`) but nothing for subscribe/unsubscribe events.
- New Gold model required: a `fct_klaviyo_subscriber_growth` monthly fact (one row per `store_id` per month). This is the "dbt work" below. **This model is shared with tickets 017 (12-month subscriber growth totals) and 019 (12-month subscriber growth monthly table).** Whichever of 017, 018, 019 runs first builds the model; the later two reuse it and add no new dbt work. Do not pretend the model already exists, and do not build a second model for the same data.

## dbt work
- **If `fct_klaviyo_subscriber_growth` does not yet exist (tickets 017, 018, 019 share it):** create `dbt/models/gold/fct_klaviyo_subscriber_growth.sql`.
  - Read from `stg_klaviyo__events` joined to `stg_klaviyo__metrics` on `metric_id` to resolve the metric name. Filter to the two subscribe/unsubscribe metrics (match on the Klaviyo metric name: "Subscribed to Email Marketing" and "Unsubscribed from Email Marketing"; confirm the exact strings with the Snowflake fallback SQL, Klaviyo metric naming can vary).
  - Grain: one row per `store_id` per month. Columns: `store_id`, `order_month` (`date_trunc('month', occurred_at)::date`, named `order_month` so the dashboard Month filter can cross-apply, see generator section (d)), `subscribed_count`, `unsubscribed_count`, `net_subscribers` (`subscribed_count - unsubscribed_count`).
  - Compute the counts with conditional aggregation: `count_if(metric_name = 'Subscribed to Email Marketing') as subscribed_count`, `count_if(metric_name = 'Unsubscribed from Email Marketing') as unsubscribed_count`, grouped by `store_id` and the month.
  - Add a surrogate key `subscriber_growth_id` (e.g. `{{ dbt_utils.generate_surrogate_key(['store_id', 'order_month']) }}`) so the model has a clean unique key.
- Add the model to `dbt/models/gold/_schema.yml` with: `not_null` and `unique` on `subscriber_growth_id`; `not_null` on `store_id` and `order_month`; a range / `dbt_utils.accepted_range` test asserting `subscribed_count >= 0` and `unsubscribed_count >= 0`.
- After creating the model, `cd dbt && dbt build --select fct_klaviyo_subscriber_growth+` and confirm tests pass.
- If `fct_klaviyo_subscriber_growth` already exists (ticket 017 or 019 built it first), write "no dbt changes needed" and proceed straight to the Lightdash work.

## Lightdash work
- **Tile type:** vertical bar chart. A 12-month trend is a time series, so the bars run vertically with `order_month` on the x-axis (one bar per month) and `net_subscribers` on the y-axis. This is the deliberate exception to the project's default of horizontal bars (the horizontal-bar default is for category bars, not time series).
- **Placement:** on the iS Clinical KPI Report dashboard, in the subscriber-growth block that mirrors PDF page 18. It sits directly below the 12-month subscriber growth totals KPI strip (ticket 017) and above the 12-month subscriber growth monthly table (ticket 019), reproducing the PDF page order: totals, then chart, then table.
- **Chart YAML:** check `lightdash/charts/` first for an existing subscriber-growth chart to adapt. None exists today (the only Klaviyo / CRM charts are `klaviyo-bridge-contacts-with-klaviyo-profile.yml`, `crm-customers-b2b-vs-b2c.yml`, `top-dtc-spenders-crm-presence-flags.yml`), so create `lightdash/charts/subscriber-growth-monthly-bar-chart.yml`. It charts the new `fct_klaviyo_subscriber_growth` explore: x-axis dimension `order_month`, y-axis metric `net_subscribers` (a `sum` metric on the column), `chartType: cartesian` with `bar` series, vertical orientation (do **not** set `flipAxes: true`). Optionally apply a conditional colour so positive bars render green and negative bars red, matching the PDF; if Lightdash cannot express per-bar conditional colour cleanly, a single neutral colour is acceptable, the sign is already legible from the axis.
- **Dashboard YAML:** update `lightdash/dashboards/kpi-report.yml` to add the chart tile in the subscriber-growth block.
- **Mandatory Source comment:** every chart and dashboard YAML file you create or edit must have, as its first line, the exact comment `# Source: April 2026 KPI Report, page 18 (iS Clinical, 12-month subscriber growth)`.
- **Month filter relationship (important, this is a trend chart not a single-month metric):** the dashboard Month filter is a single-month filter (`fct_orders_order_month_label`, default `2026-04`). This tile must **not** collapse to a single month when the filter is set, it must always show a rolling 12-month series. Two acceptable approaches, pick whichever the live YAML supports cleanly:
  1. **Exclude this tile from the Month filter** by not adding a `tileTargets` entry for it (or pointing its target at no field), so the dashboard Month filter does not cross-apply. The chart then shows all months in `fct_klaviyo_subscriber_growth` and a chart-level "last 12 months" date filter (on `order_month`) keeps it to a trailing year.
  2. **Cross-apply as a rolling window** if the live Lightdash version supports a relative / "in the last 12 months" filter target, so the Month filter shifts the 12-month window rather than slicing to one month.
  Approach 1 is the simpler and recommended default. Either way, confirm the underlying `fct_klaviyo_subscriber_growth` explore exposes `order_month` (the model creates it as `date_trunc('month', occurred_at)::date`) so it is consistent with the rest of the dashboard, and document in the YAML / PR which approach was taken and why the tile is intentionally not month-scoped.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile. Because this is a rolling 12-month chart, the Month filter should not collapse it: confirm the chart still shows 12 monthly bars.
- Assert the trailing 12-month series matches the PDF table in the "PDF reference" section above: in particular the Apr 26 bar is **+276**, the Nov 25 bar is the tallest at **+2,705**, and Aug 25 / Sep 25 are the deepest negatives at **-562** and **-588**.
- If it does not match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (wrong metric-name match, wrong month bucketing) or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`):
```sql
-- Step 1: confirm the exact Klaviyo metric names for subscribe / unsubscribe events.
select m.name, count(*) as event_count
from hgi.silver.stg_klaviyo__events e
join hgi.silver.stg_klaviyo__metrics m
  on e.metric_id = m.metric_id
where e.store_id = 'isclinical'
  and lower(m.name) like '%subscribed%email%'
group by 1
order by 2 desc;

-- Step 2: net subscribers added per month, trailing 12 months (May 2025 to Apr 2026).
-- Substitute the exact metric-name strings confirmed in step 1 if they differ.
select
    date_trunc('month', e.occurred_at)::date          as order_month,
    count_if(m.name = 'Subscribed to Email Marketing')     as subscribed_count,
    count_if(m.name = 'Unsubscribed from Email Marketing') as unsubscribed_count,
    subscribed_count - unsubscribed_count                  as net_subscribers
from hgi.silver.stg_klaviyo__events e
join hgi.silver.stg_klaviyo__metrics m
  on e.metric_id = m.metric_id
where e.store_id = 'isclinical'
  and m.name in ('Subscribed to Email Marketing', 'Unsubscribed from Email Marketing')
  and e.occurred_at >= '2025-05-01'
  and e.occurred_at <  '2026-05-01'
group by 1
order by 1;
-- Expected April 2026 row: net_subscribers = 276 (624 subscribed, 348 unsubscribed).
-- Expected 12-month totals: 8,059 subscribed, 5,774 unsubscribed, 2,285 net.
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). Creating `fct_klaviyo_subscriber_growth` adds a new Gold model; if the `CLAUDE.md` Gold-layer model list enumerates fact tables, add the new model there in the same PR. Note that this model is shared by tickets 017, 018 and 019.
