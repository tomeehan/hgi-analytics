# 014: CRM KPI strip

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-014-crm_kpi_strip`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-014-crm_kpi_strip`.
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
- Page 16, section "IS CLINICAL, 7. CRM Performance" (header reads "IS CLINICAL CRM Performance", source-of-truth tag "KLAVIYO (PLACED ORDER, 5-DAY WINDOW)").
- April 2026 value (iS Clinical): this tile is a **KPI strip**, the row of seven big numbers across the top of the CRM Performance page. The seven values are:
  - **TOTAL CRM REVENUE: £64,885** (sub-label "87.9% of GA total")
  - **CAMPAIGN REV: £50,667** (sub-label "78.1%")
  - **FLOW REV: £14,218** (sub-label "21.9%")
  - **ACTIVE PROFILES: 43,658** (sub-label "Everyone minus unsubs/bounces")
  - **ENGAGED PROFILES: 10,156** (sub-label "Engaged (30 Days)")
  - **OPEN RATE: 67.7%** and **CLICK RATE: 1.72%** (the PDF shows these as a single "OPEN / CLICK RATE 67.7% / 1.72%" stat with sub-label "111,150 delivered")
- Campaign Rev (£50,667) and Flow Rev (£14,218) sum to Total CRM Revenue (£64,885), and 78.1% + 21.9% = 100%.

## Metric definition
This tile is one KPI strip (per generator rule 5: a row of big numbers on the PDF is one tile and one ticket). It carries seven numbers:

- **Total CRM revenue** (£64,885): total Klaviyo Placed Order revenue attributed to a campaign or a flow within Klaviyo's 5-day attribution window, for iS Clinical. Equals Campaign Rev + Flow Rev.
- **Campaign revenue** (£50,667): the campaign-attributed slice of Placed Order revenue.
- **Flow revenue** (£14,218): the flow-attributed slice of Placed Order revenue.
- **Active profiles** (43,658): count of Klaviyo profiles in the "Everyone" list minus unsubscribed and bounced profiles. A point-in-time profile-base count, not a monthly event count.
- **Engaged profiles** (10,156): count of Klaviyo profiles in the "Engaged (30 Days)" segment. Also a point-in-time count.
- **Open rate** (67.7%): unique opens divided by delivered, across iS Clinical email sends in the month.
- **Click rate** (1.72%): unique clicks divided by delivered, across iS Clinical email sends in the month (111,150 delivered).
- Source of truth chain per the PDF appendix: **Klaviyo** (Placed Order events on a 5-day window for revenue; Received / Opened / Clicked Email events for open/click rate; profile lists/segments for the profile counts). All of it derives from the raw `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` table. Not Shopify, GA4, Meta or Google Ads.
- Filter behaviour: the strip is scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the revenue and rate numbers must read the April figures above. The two profile-count numbers are point-in-time snapshots and do not vary cleanly by month, see "Data dependencies".

## Data dependencies
- Bronze source needed: `BRONZE_KLAVIYO_ISCLINICAL`, status **Live** per generator section (c). No Shopify sync-gap note applies (this is a Klaviyo-sourced tile, not a Shopify-sourced one).
- **The Klaviyo data is fully present.** `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` holds 5.9M rows all-time (verified in Snowflake 2026-05-20). April 2026 carries Received Email 111,146 (the PDF's "111,150 delivered" reconciles), Opened Email 104,230, Clicked Email 3,426 and Placed Order 2,092. Every number in this strip except the two profile counts is buildable from raw `EVENTS` today. This is a **modelling gap, not a data gap**: the only empty things are the legacy Gold models `fct_klaviyo_revenue` and `fct_campaign_performance` (both 0 rows) and Klaviyo's pre-aggregated reporting streams in Bronze (`CAMPAIGN_VALUES_REPORTS`, `FLOW_SERIES_REPORTS`, deliberately not synced by Airbyte's lean stream selection). The raw `EVENTS` data is not missing.
- **`EVENTS` structure.** `EVENTS.RELATIONSHIPS:metric:data:id` joins to `METRICS.ID`; the metric name is `METRICS.ATTRIBUTES:name` (`Received Email`, `Opened Email`, `Clicked Email`, `Placed Order`). The payload is in `EVENTS.ATTRIBUTES:event_properties` and `EVENTS.DATETIME` is the event timestamp. Engagement events (Received / Opened / Clicked Email) carry `$message`, `$campaign`, `$flow` and `Campaign Name` in `event_properties`. Placed Order events carry `$value` and `$currency_code` but **no** `$campaign` / `$flow` / `$message`.
- Silver and Gold models in scope:
  - `dbt/models/gold/fct_klaviyo_revenue.sql`: Gold fact, grain one row per Placed Order event, with `revenue`, `attribution_kind`, `campaign_id`, `flow_id`, `order_month`, `store_id`. Backs total CRM revenue (and, sliced by `attribution_kind`, the campaign and flow splits). Currently 0 rows: the model must be rebuilt off raw `EVENTS` with a 5-day-window attribution, see "dbt work".
  - `dbt/models/gold/fct_campaign_performance.sql`: Gold fact intended to back open rate and click rate. Currently 0 rows: open and click rate must instead be derived directly from the Received / Opened / Clicked Email event counts (no attribution join), see "dbt work".
  - `dbt/models/silver/stg_klaviyo__metrics.sql`, `dbt/models/silver/stg_klaviyo__events.sql`: the Silver staging layer over `EVENTS` and `METRICS`.
  - `dbt/models/silver/stg_klaviyo__placed_orders.sql`, `dbt/models/silver/stg_klaviyo__campaign_stats.sql`: the Silver staging models the two Gold facts select from.
- **Revenue numbers (total / campaign / flow) are buildable now.** Total CRM revenue and the campaign-vs-flow split are an attribution computation directly on raw `EVENTS`: attribute each Placed Order's `$value` to the campaign or flow of the same profile's most recent email engagement within a 5-day window. There is no prerequisite data-engineering ticket and no dependency on the disabled reporting streams. The PDF figures (campaign `£50,667`, flow `£14,218`, total `£64,885`) are reproducible from the raw events once the Gold model is rebuilt, see "dbt work".
- **Open rate and click rate are buildable now and do not need the attribution join.** Derive them directly from the `Received` / `Opened` / `Clicked Email` event counts for the month: open rate = unique opens / delivered, click rate = unique clicks / delivered. April 2026's 111,146 Received Email events reconcile with the PDF's "111,150 delivered".
- **Active / engaged profiles are the harder sub-metric.** There is no Gold model for **active profiles** (43,658) or **engaged profiles** (10,156). Those are point-in-time profile/segment counts ("Everyone" minus unsubs/bounces; the "Engaged (30 Days)" segment), sourced from the Klaviyo `PROFILES` table or Klaviyo segments, not from events. They are point-in-time snapshots, so they do not respond cleanly to the dashboard Month filter the way a revenue total does. Treat the two profile counts as **the trickier sub-metric, out of scope for the live tile** in the first pass: either omit them from the strip, or render them as static markdown sourced from the PDF (clearly labelled as a point-in-time PDF figure). Modelling Klaviyo profiles/segments into Silver/Gold is a separate follow-up. Note this explicitly in the PR and the Basecamp closing comment.
- New Silver or Gold models or columns required: see "dbt work" below. Both `fct_klaviyo_revenue` and `fct_campaign_performance` need to be rebuilt off raw `EVENTS`, and the campaign-performance explore needs a Month dimension named to match the dashboard filter.

## dbt work
- **Rebuild `dbt/models/gold/fct_klaviyo_revenue.sql` (and its Silver feeders) off raw `EVENTS`.** The model currently returns 0 rows. It must be rebuilt to compute attribution directly from `BRONZE_KLAVIYO_ISCLINICAL.EVENTS`, not from the disabled reporting streams:
  - In Silver, isolate Placed Order events (`$value`, `$currency_code`, profile id, `DATETIME`) and engagement events (Received / Opened / Clicked Email, carrying `$message`, `$campaign`, `$flow`, `Campaign Name`, profile id, `DATETIME`). Join to `stg_klaviyo__metrics` on `RELATIONSHIPS:metric:data:id` to resolve metric names.
  - For each Placed Order, find the same profile's most recent email engagement within a 5-day window before the order; carry its `$campaign` / `$flow` onto the order as `attribution_kind` (`campaign` or `flow`) plus `campaign_id` / `flow_id`. Orders with no qualifying engagement fall outside the campaign/flow split.
  - The Gold fact keeps its existing shape (`revenue`, `attribution_kind`, `campaign_id`, `flow_id`, `order_month`, `order_month_label`, `store_id`, `total_klaviyo_revenue` metric) so the Lightdash charts wire up unchanged. Verify against the Snowflake fallback SQL: campaign `£50,667`, flow `£14,218`, total `£64,885`.
- **Rebuild the open-rate / click-rate path off raw `EVENTS`.** `fct_campaign_performance` is also empty. Open and click rate do not need the attribution join: derive them straight from the engagement event counts. In Silver, aggregate Received / Opened / Clicked Email events per month (and, if a per-campaign grain is wanted, per `$campaign`), then in Gold expose `delivered` (Received Email count), `unique_opens`, `unique_clicks`, and the `avg_open_rate` / `avg_click_rate` / `total_delivered` metrics. April 2026 must reconcile to delivered `111,146` (PDF "111,150"), open rate `~67.7%`, click rate `~1.72%`.
- **`dbt/models/gold/_schema.yml`: add a Month dimension to `fct_campaign_performance`.** The open-rate and click-rate halves of this strip read from `fct_campaign_performance`. The dashboard Month filter is keyed on `order_month_label` (compact `YYYY-MM`). To let the filter cross-apply by field name, add an additional dimension `order_month_label` on `fct_campaign_performance` with `type: string` and `sql: "to_char(${TABLE}.send_month, 'YYYY-MM')"`, mirroring the `order_month_label` additional dimension already defined on `fct_klaviyo_revenue` and `fct_orders`.
- Tests to add: keep `not_null` + `unique` on `fct_klaviyo_revenue.event_id`, `not_null` on `store_id` and `order_month`, and the `accepted_range` (`min_value: 0`) on `revenue`. Keep `not_null` on `fct_campaign_performance.campaign_id` and `store_id`. Add an `accepted_range` (`min_value: 0`) on `delivered` / `unique_opens` / `unique_clicks` if not already present. The derived `order_month_label` dimension needs no key test.
- The two profile counts (active, engaged) require no dbt work in this ticket because they are the harder sub-metric and out of scope for the live tile (see "Data dependencies"). If a follow-up ticket models Klaviyo profiles/segments, that ticket adds the Gold model and tests.

## Lightdash work
- Tile type: **KPI strip**, implemented in Lightdash as a row of **big number** tiles (one big-number chart per metric), since Lightdash has no native multi-stat strip tile. It sits on the iS Clinical KPI Report dashboard under the **CRM Performance** heading, mirroring page 16 of the PDF: the strip is the first row of that section, above the campaign and flow tables built by tickets 015 and 016.
- Charts to create or adapt (one `lightdash/charts/<slug>.yml` file per metric in the strip):
  - `lightdash/charts/isclinical-crm-total-revenue.yml`: big number, `fct_klaviyo_revenue` explore, metric `total_klaviyo_revenue`, no `attribution_kind` filter (sums campaign + flow).
  - `lightdash/charts/isclinical-crm-campaign-revenue.yml`: big number, `fct_klaviyo_revenue` explore, metric `total_klaviyo_revenue`, with a chart-level filter `attribution_kind = 'campaign'`.
  - `lightdash/charts/isclinical-crm-flow-revenue.yml`: big number, `fct_klaviyo_revenue` explore, metric `total_klaviyo_revenue`, with a chart-level filter `attribution_kind = 'flow'`.
  - `lightdash/charts/isclinical-crm-open-rate.yml`: big number, `fct_campaign_performance` explore, metric `avg_open_rate` (format `percent`, 1 dp).
  - `lightdash/charts/isclinical-crm-click-rate.yml`: big number, `fct_campaign_performance` explore, metric `avg_click_rate` (format `percent`, 1 dp).
  - Active profiles (43,658) and engaged profiles (10,156): **not built as live charts** in this pass (see "Data dependencies", gap 2). Either omit them, or add them inside a small markdown tile labelled clearly as point-in-time PDF figures. Do not fake them with a query.
  - Before creating any new chart YAML, check `lightdash/charts/` for an existing big-number chart to adapt. The big-number charts from tickets 001 to 004 (Shopify Revenue, Shopify Orders, Meta Spend, Klaviyo Revenue) are the closest templates; adapt the Klaviyo Revenue chart in particular since it already targets `fct_klaviyo_revenue`.
- Update `lightdash/dashboards/kpi-report.yml` to place the strip's tiles in one row under a CRM Performance section heading.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its very first line, the comment `# Source: April 2026 KPI Report, page 16 (IS CLINICAL, 7. CRM Performance)`.
- How the tiles pick up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`.
  - `fct_klaviyo_revenue` already exposes a matching `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`), so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_klaviyo_revenue_order_month_label` via `tileTargets` for the three revenue tiles.
  - `fct_campaign_performance` does **not** currently expose a `YYYY-MM` month label, only `send_month`. The "dbt work" section adds an `order_month_label` additional dimension to it; after that change, cross-apply the Month filter onto `fct_campaign_performance_order_month_label` via `tileTargets` for the open-rate and click-rate tiles. Confirm `order_month_label` is present on both explores after `lightdash download` before editing the dashboard YAML.

## Preview verification
Verify the strip in the preview project (step 5 of the workflow) against the PDF numbers:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read each big number in the strip.
- Assert:
  - Total CRM revenue tile = `£64,885`
  - Campaign revenue tile = `£50,667`
  - Flow revenue tile = `£14,218`
  - Open rate tile = `67.7%`
  - Click rate tile = `1.72%`
- If a tile does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (most likely a mistake in the attribution logic) and fix it before merging.
  - All five revenue and rate tiles read from Gold models rebuilt off raw `EVENTS` (see "dbt work"). The raw Klaviyo data is fully present, so every one of them is expected to match the PDF and must be verified properly. There is no expected `£0` gap and no prerequisite data-engineering ticket.
  - The active-profiles and engaged-profiles numbers are the harder sub-metric and out of scope for the live tile (see "Data dependencies"): do not block merge on them, but record their status in the closing comment.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`). Once `fct_klaviyo_revenue` and `fct_campaign_performance` are rebuilt (see "dbt work"), the same checks can run against the Gold models; the queries below go straight to raw `EVENTS` so they work even before the rebuild and prove the data is present.

First confirm the April 2026 event volumes (the proof the data is fully present):
```sql
select m.attributes:name::string as metric_name,
       count(*)                  as events
from HGI.BRONZE_KLAVIYO_ISCLINICAL.EVENTS e
join HGI.BRONZE_KLAVIYO_ISCLINICAL.METRICS m
  on m.id = e.relationships:metric:data:id::string
where e.datetime >= '2026-04-01' and e.datetime < '2026-05-01'
group by 1
order by 2 desc;
```
Expected: `Received Email` ~111,146 (PDF "111,150 delivered"), `Opened Email` ~104,230, `Clicked Email` ~3,426, `Placed Order` ~2,092.

Open rate and click rate (straight from the engagement event counts, no attribution join):
```sql
with ev as (
    select m.attributes:name::string as metric_name
    from HGI.BRONZE_KLAVIYO_ISCLINICAL.EVENTS e
    join HGI.BRONZE_KLAVIYO_ISCLINICAL.METRICS m
      on m.id = e.relationships:metric:data:id::string
    where e.datetime >= '2026-04-01' and e.datetime < '2026-05-01'
)
select
    div0(count_if(metric_name = 'Opened Email'),  count_if(metric_name = 'Received Email')) as open_rate,
    div0(count_if(metric_name = 'Clicked Email'), count_if(metric_name = 'Received Email')) as click_rate,
    count_if(metric_name = 'Received Email')                                               as delivered
from ev;
```
Expected per the PDF: open rate `~0.677` (67.7%), click rate `~0.0172` (1.72%), delivered `~111,146`.

Total / campaign / flow CRM revenue (5-day-window attribution on raw events): attribute each `Placed Order` `$value` to the campaign or flow of the same profile's most recent engagement event in the prior 5 days, then roll up. Expected per the PDF: campaign `50667`, flow `14218`, total `64885`. After the `fct_klaviyo_revenue` rebuild this is simply:
```sql
select
    coalesce(attribution_kind, 'total') as attribution_kind,
    sum(revenue)                        as revenue
from HGI.GOLD.FCT_KLAVIYO_REVENUE
where store_id = 'isclinical'
  and order_month = '2026-04-01'
group by rollup (attribution_kind)
order by attribution_kind;
```
Note the PDF rates are aggregate (sum of unique opens / sum of delivered); the Lightdash `avg_open_rate` / `avg_click_rate` metrics are an average of per-row rates, so small rounding differences are acceptable. If the divergence is large, consider whether the tile should use a weighted ratio metric instead and note it in the ticket.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket on its own does not introduce a new source or schema. Rebuilding `fct_klaviyo_revenue` and `fct_campaign_performance` off raw `EVENTS` (with the 5-day-window attribution) is a convention worth recording: note in `CLAUDE.md` that Klaviyo Gold facts are modelled from the raw `EVENTS` stream, not from Klaviyo's pre-aggregated reporting streams (which are deliberately not synced). If a follow-up ticket models Klaviyo profiles/segments, record that resolution too.
