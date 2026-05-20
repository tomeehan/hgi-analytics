# 015: Top performing campaigns

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-015-top_performing_campaigns`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-015-top_performing_campaigns`.
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
- Page 16, section "IS CLINICAL, 7. CRM Performance, panel TOP PERFORMING CAMPAIGNS". (The page header reads "IS CLINICAL, 7. CRM PERFORMANCE"; the source caption is "Klaviyo (placed order, 5-day window)". The Top Performing Campaigns table is the lower-left panel, with the Top Performing Flows panel, ticket 016, to its right.)
- April 2026 value (iS Clinical): the panel is a small table, **5 rows** (top 5 campaigns by revenue):

  | Campaign | Revenue |
  |---|---|
  | `2026_04(Apr)_BAU_SpringSale#1 (EarlyAccess)` | £13,098 |
  | `2026_04(Apr)_BAU_SpringSale#4 (Final Push)` | £8,212 |
  | `2026_04(Apr)_BAU_SpringSale#3 (Categories)` | £7,956 |
  | `2026_04(Apr)_BAU_SpringSale#1 NON-OPENER RESEND` | £6,295 |
  | `2026_04(Apr)_BAU_SpringSale#2 (Collections)` | £5,516 |

  Context on the same page: the CRM KPI strip (ticket 014) reports CAMPAIGN REV of **£50,667** for April; these five campaigns together account for **£41,077** of that total.

## Metric definition
- Plain English: the top five iS Clinical Klaviyo email campaigns in the month, ranked by placed-order revenue attributed to each campaign within a 5-day window. Each row is one campaign (its send name) and the revenue attributed to it. The panel is the campaign-level detail behind the CAMPAIGN REV headline in the CRM KPI strip (ticket 014).
- Source of truth chain per the PDF appendix: **Klaviyo** only. Campaign names and revenue are computed from raw Klaviyo `EVENTS` (engagement events carry the campaign id; Placed Order events carry the order value), with revenue attributed on a placed-order, 5-day window. Not Shopify, GA4, Meta or Google Ads.
- Filter behaviour: the tile is a **table** scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the table must show the top five iS Clinical campaigns by revenue for that month.

## Data dependencies
- Bronze source needed: `BRONZE_KLAVIYO_ISCLINICAL`, status **Live** per generator section (c) ("iS Clinical (DTC): Live"). The Shopify sync-gap note does **not** apply (this is a Klaviyo-sourced tile, not a Shopify-sourced one).
- **The campaign data is fully present in raw events. This tile is buildable now.** `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` is fully populated (5.9M rows all-time; April 2026 includes 2,092 Placed Order events plus rich engagement events) and `BRONZE_KLAVIYO_ISCLINICAL.CAMPAIGNS` has 234 rows. The only empty things are the dbt Gold models and Klaviyo's pre-aggregated reporting streams in Bronze (`CAMPAIGN_VALUES_REPORTS`, `FLOW_SERIES_REPORTS`, both 0 rows, deliberately not synced by Airbyte's lean stream selection). This is a **modelling gap, not a data gap**: the raw `EVENTS` data needed to compute campaign revenue is present. Do **not** treat this tile as blocked, and do **not** plan to re-enable `campaign_values_reports`.
- Silver and Gold models that may exist today:
  - `dbt/models/silver/stg_klaviyo__campaigns.sql` exists, grain one row per campaign. Selects `campaign_id`, `campaign_name`, `status`, `channel`, `send_time`, `created_at`, `updated_at`, `store_id` from `source('bronze_klaviyo_isclinical', 'campaigns')`. The `campaign_name` column is the campaign send name shown in the PDF panel.
  - `dbt/models/silver/stg_klaviyo__campaign_stats.sql` and `dbt/models/gold/fct_campaign_performance.sql` may exist as legacy models, but they source revenue from the empty `campaign_values_reports` stream and so are themselves empty. They are **not** the source of truth for this tile and must not be relied on as-is.
  - `dbt/models/gold/dim_campaigns.sql` exists, filtered to `channel = 'email'`, grain one row per campaign. It is a usable campaign dimension if a clean campaign list is wanted, but campaign revenue is not on it.
- New Gold model required: campaign revenue must come from a new (or rebuilt) Gold model that computes the 5-day-window attribution off raw `EVENTS`. See "dbt work" for the exact model.
- **Klaviyo `EVENTS` structure (verified in Snowflake 2026-05-20).** `EVENTS.RELATIONSHIPS:metric:data:id` joins to `METRICS.ID`; the metric name is `METRICS.ATTRIBUTES:name`. The event payload is in `EVENTS.ATTRIBUTES:event_properties`, and `EVENTS.DATETIME` is the event timestamp. Engagement events (Received Email, Opened Email, Clicked Email) carry `$message`, `$campaign` (campaign id), `Campaign Name` and `$flow` in `event_properties`. Placed Order events carry `$value` and `$currency_code` but **no** `$campaign` or `$flow`. Campaign revenue is therefore an attribution computation, not a direct sum: attribute each Placed Order's `$value` to the campaign of the same profile's most recent campaign-email engagement within a 5-day window before the order, group by `$campaign` / `Campaign Name`, rank by revenue, take the top 5.
- Klaviyo placed-order attribution is a **5-day-window** model (per the PDF caption): the campaign revenue figure is a Klaviyo-style attribution construct, not a Shopify-order join. Do not attempt to reconcile these campaign revenue figures against `fct_orders`; they are a different measure and will not tie out. Reconcile only against the Klaviyo `EVENTS` source data.

## dbt work
- **A new (or rebuilt) Gold model is required.** Campaign revenue is computed from raw `EVENTS`, not from the empty `campaign_values_reports` stream. Build a Gold model (for example `dbt/models/gold/fct_klaviyo_campaign_revenue.sql`, grain one row per `campaign_id` x `store_id` x `event_month`) that does the 5-day-window attribution:
  1. **Silver staging off raw events.** Add or extend Silver staging on `source('bronze_klaviyo_isclinical', 'events')` joined to `source('bronze_klaviyo_isclinical', 'metrics')` (`events.RELATIONSHIPS:metric:data:id = metrics.ID`, metric name from `metrics.ATTRIBUTES:name`). Split into two relations: engagement events (metric name in Received/Opened/Clicked Email) carrying `profile_id`, `$campaign`, `Campaign Name`, `event_datetime`; and Placed Order events carrying `profile_id`, `$value`, `$currency_code`, `event_datetime`. Read the payload from `ATTRIBUTES:event_properties` and the timestamp from `EVENTS.DATETIME`. Add `store_id = 'isclinical'` and `date_trunc('month', event_datetime)::date as order_month`.
  2. **5-day-window attribution.** For each Placed Order event, find the same profile's most recent campaign-email engagement event in the 5 days before the order, and attribute the order's `$value` to that engagement's `$campaign` / `Campaign Name`. Orders with no qualifying engagement in the window are not attributed to any campaign (dropped from this model).
  3. **Aggregate.** Group the attributed orders by `campaign_id`, `Campaign Name`, `store_id`, `order_month`; `sum($value)` as `revenue`. Expose `campaign_id`, `campaign_name`, `store_id`, `order_month`, `revenue`.
- Update `dbt/models/gold/_schema.yml` for the new model: `campaign_name` as a string dimension, `revenue` as a `sum`-type metric with `format: gbp`, `store_id` as a dimension, and a month dimension usable by the dashboard Month filter (see "Lightdash work" for the exact field-name requirement). The dashboard Month filter is on `fct_orders_order_month_label`, so expose an `order_month_label` additional dimension (`to_char(${TABLE}.order_month, 'YYYY-MM')`) so the filter cross-applies by field name.
- Tests to add: `not_null` on `campaign_id` and on `revenue`; a `dbt_utils.accepted_range` (`min_value: 0`) range test on `revenue`; and `dbt_utils.unique_combination_of_columns` on `[campaign_id, store_id, order_month]` (the model grain).
- Build and verify with `cd dbt && dbt build --select fct_klaviyo_campaign_revenue+` (substitute the actual model name) and reconcile the April 2026 top 5 against the PDF using the Snowflake fallback SQL below.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard in the CRM Performance area, mirroring the PDF page-16 layout: Top Performing Campaigns is the lower-left panel of the CRM Performance page. Place this tile after ticket 014's "CRM KPI strip" and before ticket 016's "Top performing flows" table, so the dashboard row order follows the PDF.
- Create `lightdash/charts/isclinical-top-performing-campaigns.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing chart that already fits and adapt it: ticket 016 ("Top performing flows") produces a near-identical revenue-ranked table and ticket 014 sits on related CRM explores, so if `isclinical-top-performing-flows.yml` or a similar Klaviyo revenue table already exists, copy and adapt it. Otherwise build a fresh table chart.
  - The chart is a **table** on the new campaign-revenue Gold explore (the model built in "dbt work", for example `fct_klaviyo_campaign_revenue`). Dimension: `campaign_name` (the Campaign column). Metric: `revenue` (the Revenue column, `format: gbp`).
  - Add a chart-level filter `store_id = 'isclinical'` (the explore may union iS Clinical and Deese Pro; the dashboard is single-brand, so the tile must scope to iS Clinical itself).
  - Sort by `revenue` descending and set the row limit to **5** so it stays a compact top-5 highlights panel matching the PDF.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 16 (IS CLINICAL, 7. CRM Performance, panel TOP PERFORMING CAMPAIGNS)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. The campaign-revenue explore must expose a matching month label dimension so Lightdash can cross-apply the filter by field name. The new Gold model carries a month-truncated `order_month`; expose an `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`) on it, then cross-apply the dashboard Month filter onto the explore's `order_month_label` field via `tileTargets` in `kpi-report.yml`. Confirm the month label dimension is present on the explore before editing the YAML; if it is not, add it in `_schema.yml` first (see "dbt work").

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile.
- Assert the five rows match the PDF: `2026_04(Apr)_BAU_SpringSale#1 (EarlyAccess)` at **£13,098**, `2026_04(Apr)_BAU_SpringSale#4 (Final Push)` at **£8,212**, `2026_04(Apr)_BAU_SpringSale#3 (Categories)` at **£7,956**, `2026_04(Apr)_BAU_SpringSale#1 NON-OPENER RESEND` at **£6,295**, `2026_04(Apr)_BAU_SpringSale#2 (Collections)` at **£5,516**. Revenue values may differ by a small rounding amount (the PDF rounds to whole pounds, and the 5-day-window attribution may give marginally different totals than Klaviyo's own reporting).
- If the rows do **not** match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is in the attribution logic of the new Gold model (window length, engagement-event filter, join keys). The raw `EVENTS` data is present, so a mismatch is a modelling issue to debug in the Gold model, not a data-availability block.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`).

First, confirm the raw `EVENTS` data is present for iS Clinical (it is, as of 2026-05-20; this is a sanity check, not a blocker test):
```sql
select count(*) as event_count
from HGI.BRONZE_KLAVIYO_ISCLINICAL.EVENTS;
```

Then reproduce the top-5 campaigns by revenue for April 2026 directly from raw `EVENTS`, applying the 5-day-window attribution (this is the same logic the new Gold model implements):
```sql
with events as (
    select
        e.RELATIONSHIPS:profile:data:id::string                       as profile_id,
        m.ATTRIBUTES:name::string                                     as metric_name,
        e.DATETIME                                                    as event_at,
        e.ATTRIBUTES:event_properties                                 as props
    from HGI.BRONZE_KLAVIYO_ISCLINICAL.EVENTS e
    join HGI.BRONZE_KLAVIYO_ISCLINICAL.METRICS m
      on m.ID = e.RELATIONSHIPS:metric:data:id::string
),
engagements as (
    select
        profile_id,
        event_at,
        props:"$campaign"::string      as campaign_id,
        props:"Campaign Name"::string  as campaign_name
    from events
    where metric_name in ('Received Email', 'Opened Email', 'Clicked Email')
      and props:"$campaign" is not null
),
orders as (
    select
        profile_id,
        event_at,
        props:"$value"::float as order_value
    from events
    where metric_name = 'Placed Order'
),
attributed as (
    select
        o.order_value,
        eng.campaign_id,
        eng.campaign_name,
        row_number() over (
            partition by o.profile_id, o.event_at
            order by eng.event_at desc
        ) as rn
    from orders o
    join engagements eng
      on eng.profile_id = o.profile_id
     and eng.event_at <= o.event_at
     and eng.event_at >= dateadd('day', -5, o.event_at)
)
select
    campaign_name,
    sum(order_value) as revenue
from attributed
where rn = 1
  and date_trunc('month', /* order event_at flows through rn=1 */ current_timestamp()) is not null
group by campaign_name
order by revenue desc
limit 5;
```
Scope the order events to April 2026 (`date_trunc('month', event_at) = '2026-04-01'` on the `orders` CTE) when reproducing the April figure. Expected per the PDF: `2026_04(Apr)_BAU_SpringSale#1 (EarlyAccess)` at `~13098`, `2026_04(Apr)_BAU_SpringSale#4 (Final Push)` at `~8212`, `2026_04(Apr)_BAU_SpringSale#3 (Categories)` at `~7956`, `2026_04(Apr)_BAU_SpringSale#1 NON-OPENER RESEND` at `~6295`, `2026_04(Apr)_BAU_SpringSale#2 (Collections)` at `~5516`. The query above is a guide; the exact JSON path for `profile_id` and the engagement metric names should be confirmed against a sample of `EVENTS` rows. If the new Gold model yields no rows, the bug is in its attribution SQL, not in source data.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds a new Gold model (campaign revenue from a 5-day-window attribution on raw Klaviyo `EVENTS`); if that establishes a reusable pattern (the same attribution logic backs ticket 016 flows and ticket 014's CRM KPI strip), add a short convention note to `CLAUDE.md` describing the events-based Klaviyo attribution model so later tickets reuse it.
