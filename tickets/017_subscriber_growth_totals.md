# 017: 12-month subscriber growth totals

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-017-subscriber_growth_totals`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-017-subscriber_growth_totals`.
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
- Page 17, section "12-month subscriber growth" (the iS Clinical brand section; the per-month table that backs the totals begins on page 17 and continues onto page 18, where the "12-month total" row sits).
- April 2026 value (iS Clinical): this tile is a row of three trailing-12-month big numbers, not a single April figure. The verification targets are: **12-month subs added +8,059**, **12-month unsubscribes -5,774**, **net change (12 months) +2,285**. The window stated on the PDF is May 2025 to April 2026.

## Metric definition
- Three big numbers summarising email list growth for iS Clinical over a trailing 12-month window:
  - **Subs added**: count of Klaviyo "Subscribed to Email Marketing" events in the window.
  - **Unsubscribes**: count of Klaviyo "Unsubscribed from Email Marketing" events in the window (shown as a negative number on the PDF).
  - **Net change**: subs added minus unsubscribes (`+8,059 - 5,774 = +2,285`).
- Source of truth chain per the PDF appendix: **Klaviyo**. The PDF section subtitle reads "Klaviyo (subscribed / unsubscribed events, May 2025 to Apr 2026)". No Shopify, GA4, Meta or Google Ads involvement.
- Filter behaviour: this is a **trailing-12-month** metric, not a single-calendar-month metric. It deliberately does **not** follow the dashboard Month filter. The tile always shows the rolling 12 months ending at the report's reference month (April 2026). See the "Lightdash work" section for how this is handled.

## Data dependencies
- Bronze sources needed: `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` and `BRONZE_KLAVIYO_ISCLINICAL.METRICS`. Both are **ok loaded** per generator section (c) (iS Clinical Klaviyo DTC is Live). The `events` and `metrics` tables are both declared in `dbt/models/bronze/_sources.yml` under the `bronze_klaviyo_isclinical` source.
- No Shopify involvement, so the iS Clinical Shopify sync-gap note does **not** apply to this ticket.
- Silver models that already cover this:
  - `dbt/models/silver/stg_klaviyo__events.sql`: unions Klaviyo events across iSC and Deese PRO; exposes `event_type`, `occurred_at`, `metric_id`, `store_id`, `profile_id`. Verified to exist.
  - `dbt/models/silver/stg_klaviyo__metrics.sql`: unions the Klaviyo metrics catalogue across iSC and Deese PRO; exposes `metric_id`, `metric_name`, `store_id`. Verified to exist. The human-readable `metric_name` is how "Subscribed to Email Marketing" / "Unsubscribed from Email Marketing" are identified; the join key is `(store_id, metric_id)`.
- Gold state: there is **no Gold subscriber model**. Verified: `dbt/models/gold/` contains `fct_klaviyo_revenue.sql` and `fct_campaign_performance.sql` but **no** `fct_klaviyo_subscriber_growth`. The grep hits for "subscriber" inside `stg_klaviyo__campaign_stats.sql` and `fct_campaign_performance.sql` are per-campaign recipient/unsubscribe counts, not subscriber-growth events, and are not reusable here.
- New Gold model required: `fct_klaviyo_subscriber_growth` (monthly grain). See "dbt work".

## dbt work
- **Create `dbt/models/gold/fct_klaviyo_subscriber_growth.sql`.** A new Gold fact at **monthly grain** (one row per `store_id` per month). This model is **shared with tickets 018 and 019** (the monthly bar chart and the monthly table): whichever of 017 / 018 / 019 runs first builds this model, and the later tickets reuse it as-is. Do not duplicate it.
  - Read from `stg_klaviyo__events` joined to `stg_klaviyo__metrics` on `(store_id, metric_id)`.
  - Filter `metric_name in ('Subscribed to Email Marketing', 'Unsubscribed from Email Marketing')`.
  - Add `date_trunc('month', occurred_at)::date as order_month` so the model carries a month dimension (per generator section (d): Klaviyo has no native month concept, so Silver/Gold must add one).
  - Aggregate to one row per `(store_id, order_month)` with columns: `subscribers_added` (count of "Subscribed" events), `unsubscribes` (count of "Unsubscribed" events), `net_subscriber_change` (`subscribers_added - unsubscribes`).
  - Surrogate primary key: `{{ dbt_utils.generate_surrogate_key(['store_id', 'order_month']) }} as subscriber_growth_id`.
- **Tests** (add to `dbt/models/gold/_schema.yml`): `not_null` + `unique` on `subscriber_growth_id`; `not_null` on `store_id`, `order_month`; range tests (`dbt_utils.accepted_range` with `min_value: 0`) on `subscribers_added` and `unsubscribes`. `net_subscriber_change` is signed so no range test there.
- Note: the trailing-12-month window for this ticket's three totals is a query-time / Lightdash concern (a metric over the last 12 monthly rows). The Gold model stays at simple monthly grain so 018 and 019 can reuse it without a window baked in.

## Lightdash work
- Tile type: **big number row** (one tile rendering three big numbers, per generator rule 5: a KPI strip is one tile and one ticket). It sits in the **iS Clinical brand section** of the dashboard, mirroring PDF page 17, under a "12-month subscriber growth" heading. Place it directly **above** the ticket 018 monthly bar chart and ticket 019 monthly table, matching the PDF reading order.
- The `lightdash/charts/subscriber-growth-totals.yml` file: create it (one file per tile). First check `lightdash/charts/` for an existing big-number-row chart on a Klaviyo explore to adapt before writing a new one. The chart reads from the `fct_klaviyo_subscriber_growth` explore and surfaces three metrics: total `subscribers_added`, total `unsubscribes`, total `net_subscriber_change`, each summed over the trailing 12 months.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile in the subscriber-growth row.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 17 (12-month subscriber growth)`.
- **Month filter behaviour (important):** this tile is a **trailing-12-month** metric and is **intentionally not driven by the single-month dashboard filter**. Two parts to this:
  1. The dashboard Month filter targets `fct_orders_order_month_label`. For tiles on other explores it cross-applies via `tileTargets`. For this tile, **do not** add a `tileTargets` entry mapping the Month filter onto `fct_klaviyo_subscriber_growth.order_month`. Leaving the mapping out means the dashboard Month filter does not touch this tile, which is the desired behaviour: the tile shows a fixed rolling 12-month window regardless of the selected month.
  2. The 12-month window itself is expressed in the chart's own query (a chart-level filter on `order_month` for the trailing 12 months, e.g. the 12 months ending April 2026, or `order_month >= dateadd('month', -12, ...)`). Pin the window to the report reference month so the tile reproduces the PDF's May 2025 to April 2026 figures.
  - The underlying `fct_klaviyo_subscriber_growth` explore still **exposes** `order_month` (a month-truncated dimension) so the chart-level 12-month filter can be written. It just is not wired to the dashboard-level filter via `tileTargets`.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- This tile is window-fixed, so the dashboard Month filter setting does not change it. Read the three big numbers.
- Assert they equal the trailing-12-month iS Clinical values from the "PDF reference" section: subs added **+8,059**, unsubscribes **-5,774**, net change **+2,285**.
- If they do not match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (window boundary, metric-name string, double-counted events) or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
-- iS Clinical 12-month subscriber growth totals, window May 2025 to Apr 2026.
with events as (
    select
        e.event_type,
        e.occurred_at,
        date_trunc('month', e.occurred_at)::date as order_month,
        m.metric_name
    from HGI.SILVER.STG_KLAVIYO__EVENTS e
    join HGI.SILVER.STG_KLAVIYO__METRICS m
      on e.store_id = m.store_id
     and e.metric_id = m.metric_id
    where e.store_id = 'isclinical'
      and m.metric_name in (
            'Subscribed to Email Marketing',
            'Unsubscribed from Email Marketing'
          )
      and date_trunc('month', e.occurred_at) between '2025-05-01' and '2026-04-01'
)
select
    count_if(metric_name = 'Subscribed to Email Marketing')   as subscribers_added,
    count_if(metric_name = 'Unsubscribed from Email Marketing') as unsubscribes,
    count_if(metric_name = 'Subscribed to Email Marketing')
      - count_if(metric_name = 'Unsubscribed from Email Marketing') as net_subscriber_change
from events;
-- expect: subscribers_added = 8059, unsubscribes = 5774, net_subscriber_change = 2285
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds a new Gold model `fct_klaviyo_subscriber_growth` (monthly-grain Klaviyo subscriber fact, shared with tickets 018 and 019). If 017 is the first of the three to land, add `fct_klaviyo_subscriber_growth` to the Gold model list in `CLAUDE.md`.
