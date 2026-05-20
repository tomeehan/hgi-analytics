# 006: Channel breakdown table

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-006-channel_breakdown_table`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-006-channel_breakdown_table`.
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
- Page 12, section "IS CLINICAL, 1. Revenue & Channel Attribution".
- April 2026 value (iS Clinical): the **CHANNEL (GA4)** breakdown table. Seven channel rows plus a Total row, with columns REVENUE, % OF TOTAL, SESSIONS, TRANS, VS MAR, VS APR 25:

  | Channel (GA4) | Revenue | % of total | Sessions | Trans | vs Mar | vs Apr 25 |
  |---|---|---|---|---|---|---|
  | Direct | £12,620 | 17.1% | 2,610 | 77 | +18.3% | -18.7% |
  | Organic Search | £13,686 | 18.5% | 2,980 | 101 | +66.4% | +50.6% |
  | Paid Search | £8,519 | 11.5% | 1,169 | 76 | -13.4% | -32.9% |
  | Paid Social | £4,954 | 6.7% | 1,617 | 35 | +272.4% | +450.0% |
  | Email / CRM | £11,429 | 15.5% | 1,401 | 83 | +136.5% | n/a |
  | Referral / Affiliates | £2,369 | 3.2% | 799 | 13 | +201.4% | n/a |
  | Other (Paid Shopping, Cross-network, Unassigned, Organic Social/Shopping) | £20,231 | 27.4% | 5,106 | 169 | - | - |
  | **Total** | **£73,808** | **100%** | **15,682** | **554** | **+47.2%** | **-29.8%** |

  The Total revenue (£73,808) is the GA4-attributed revenue figure that also appears in ticket 005's KPI strip. The Total sessions (15,682) matches the headline sessions number in ticket 007.

## Metric definition
- A table that decomposes iS Clinical's GA4-attributed revenue, sessions and transactions across GA4's default channel groupings, mirroring the "CHANNEL (GA4)" table on PDF page 12.
- Each row is one display channel. The seven display channels are folded down from GA4's raw `sessionDefaultChannelGrouping` values as follows:
  - `Direct` to **Direct**
  - `Organic Search` to **Organic Search**
  - `Paid Search` to **Paid Search**
  - `Paid Social` to **Paid Social**
  - `Email` to **Email / CRM**
  - `Referral` + `Affiliates` to **Referral / Affiliates**
  - everything else (`Paid Shopping`, `Cross-network`, `Unassigned`, `Organic Shopping`, `Organic Social`, `Organic Video`, `Paid Other`) to **Other**
- Source of truth chain per the PDF appendix: **GA4** only. The header on PDF page 12 labels this block "GA4 (CHANNEL ATTRIBUTION)" as distinct from the Shopify "source of truth" KPIs above it. Not Shopify, Meta, Google Ads or Klaviyo.
- Filter behaviour: the table is scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the Total row must read revenue £73,808 / sessions 15,682.
- The PDF's "% OF TOTAL", "VS MAR" and "VS APR 25" columns are presentation columns. "% OF TOTAL" is a Lightdash table calculation (row revenue / column-total revenue). The "VS MAR" and "VS APR 25" period-over-period columns are out of scope for this tile (they require March 2026 and April 2025 comparison windows that the single Month filter does not provide); the tile ships REVENUE, % OF TOTAL, SESSIONS and TRANS. Note this scope reduction in the Basecamp closing comment.

## Data dependencies
- Bronze source needed: `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL`, status **Live** per generator section (c). The specific Bronze table is `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_DEFAULT_CHANNEL_GROUPING_REPORT` (one of the 10 GA4 reports the connector loads; it carries `SESSIONDEFAULTCHANNELGROUPING`, `SESSIONS`, `TOTALREVENUE`, `EVENTCOUNT`, `ENGAGEDSESSIONS`, `TOTALUSERS` and a text `DATE` in `YYYYMMDD` format). No Shopify sync-gap note applies (this is a GA4-sourced tile, not a Shopify-sourced one).
- Silver and Gold models that already cover this: **none**. `dbt/models/silver/stg_google_analytics__sessions.sql` aggregates `TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT` across source/medium (it has no channel-grouping dimension), and `dbt/models/gold/fct_ga_sessions.sql` is a thin pass-through of it. The channel-grouping report is **not** declared as a dbt source and is **not** modelled. A new staging model and a new Gold fact are required.
- New Silver or Gold models or columns required: see "dbt work". A `bronze_google_analytics_isclinical` source table entry, a `stg_google_analytics__channel_sessions` Silver model, and a `fct_ga_channel_sessions` Gold fact.
- **Transactions caveat.** The channel-grouping Bronze report does **not** expose a per-channel purchase-event count: its `EVENTCOUNT` is the count of *all* events (page views, scrolls, etc), not purchases, so it cannot be used as the TRANS column. The PDF's per-channel TRANS values (Direct 77, Organic Search 101, etc) come from GA4's channel-grouping report joined to a `purchase`-event filter, a slice GA4's standard channel report does not return on its own. For this tile, ship REVENUE, % OF TOTAL and SESSIONS only, and add the TRANS column as a follow-up once the GA4 connector is configured to emit a channel-by-event report (or a custom purchase-by-channel report). Note this gap explicitly in the Basecamp closing comment; the PDF figures stay authoritative.

## dbt work
Channel-grouped GA4 sessions are not modelled today, so this ticket adds the path:

1. **Declare the Bronze table as a source.** In `dbt/models/bronze/_sources.yml`, under `bronze_google_analytics_isclinical`, add a table entry: `traffic_acquisition_session_default_channel_grouping_report` (alongside the existing `traffic_acquisition_session_source_medium_report` and `events_report` entries).
2. **Add `dbt/models/silver/stg_google_analytics__channel_sessions.sql`.** Model it on the existing `stg_google_analytics__sessions.sql` pattern: an `isclinical` CTE, a `unioned` CTE, then a final select. Cast the text `DATE` to a date with `to_date(date, 'YYYYMMDD')`, derive `order_month` as `date_trunc('month', session_date)::date`, set `store_id = 'isclinical'`, and fold the raw `sessiondefaultchannelgrouping` into a `channel` column via the `case` mapping in "Metric definition" (the seven display channels). Aggregate `sum(sessions) as sessions` and `sum(totalrevenue) as channel_revenue`, grouped by `session_date`, `store_id`, `channel`.
3. **Add `dbt/models/gold/fct_ga_channel_sessions.sql`.** A pass-through of the Silver model (mirror `fct_ga_sessions.sql`: `select * from {{ ref('stg_google_analytics__channel_sessions') }}` with `materialized='table'`).
4. **Schema + metrics.** Add a `stg_google_analytics__channel_sessions` block to `dbt/models/silver/_schema.yml` and a `fct_ga_channel_sessions` block to `dbt/models/gold/_schema.yml`. On the Gold model declare:
   - `not_null` tests on `session_date`, `order_month`, `store_id`, `channel`.
   - A `dbt_utils.accepted_range` (`min_value: 0`) range test on `channel_revenue` and `sessions`.
   - Metrics: `total_ga_channel_revenue` (`type: sum` on `channel_revenue`, `format: gbp`) and `total_ga_channel_sessions` (`type: sum` on `sessions`). Match the metric style already used on `fct_ga_sessions` in `dbt/models/gold/_schema.yml`.
   - An additional dimension `order_month_label` as `to_char(order_month, 'YYYY-MM')` so the dashboard Month filter cross-applies by field name (see "Lightdash work").
5. Run `cd dbt && dbt build --select stg_google_analytics__channel_sessions+ fct_ga_channel_sessions+` and confirm tests pass.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard directly under the "Revenue & channel attribution" KPI strip built by ticket 005, mirroring the PDF page 12 layout where the CHANNEL (GA4) table sits immediately below the four headline KPIs. Place it as the first full-width tile after the ticket 005 strip.
- Create `lightdash/charts/channel-breakdown-table.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing chart that already fits and adapt it instead; `revenue-by-channel-cin7.yml` is a per-channel table that is a good shape template to adapt, but it reads from a Cin7 explore so it cannot be reused directly.
  - The chart is a **table** on the `fct_ga_channel_sessions` explore, with `channel` as the row dimension, the `total_ga_channel_revenue` and `total_ga_channel_sessions` metrics as columns, and a table calculation `pct_of_total` computing `total_ga_channel_revenue / sum(total_ga_channel_revenue) over ()` formatted as a percentage for the "% OF TOTAL" column. Sort rows by `total_ga_channel_revenue` descending so "Other" lands at the bottom as in the PDF (or order to match the PDF row order if a fixed order is preferred).
  - Do not add a TRANS column: per the "Data dependencies" transactions caveat, the channel-grouping report does not expose a per-channel purchase count. Ship REVENUE, % OF TOTAL and SESSIONS.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile (full width, under the ticket 005 KPI strip).
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 12 (IS CLINICAL, 1. Revenue & Channel Attribution)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. The new `fct_ga_channel_sessions` explore must expose a matching `order_month_label` dimension (`to_char(order_month, 'YYYY-MM')`, added in "dbt work" step 4) so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_ga_channel_sessions_order_month_label` via `tileTargets` in `kpi-report.yml`. Confirm `order_month_label` is present on the `fct_ga_channel_sessions` explore before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert the Total revenue equals **£73,808** and Total sessions equals **15,682**, and that each channel row is within roughly +/-2% of the PDF values in the "PDF reference" table (small differences are expected: GA4 channel attribution is non-deterministic across report pulls and the PDF was generated from a separate GA4 export).
- If the totals are materially off, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (a bad `case` mapping, a missing channel folded into the wrong bucket) or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the channel breakdown directly from Snowflake (via `snow sql -c hgi`):
```sql
select
    case
        when sessiondefaultchannelgrouping = 'Direct'         then 'Direct'
        when sessiondefaultchannelgrouping = 'Organic Search' then 'Organic Search'
        when sessiondefaultchannelgrouping = 'Paid Search'    then 'Paid Search'
        when sessiondefaultchannelgrouping = 'Paid Social'    then 'Paid Social'
        when sessiondefaultchannelgrouping = 'Email'          then 'Email / CRM'
        when sessiondefaultchannelgrouping in ('Referral', 'Affiliates')
                                                              then 'Referral / Affiliates'
        else 'Other'
    end as channel,
    sum(sessions)                  as sessions,
    round(sum(totalrevenue), 0)    as revenue
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_DEFAULT_CHANNEL_GROUPING_REPORT
where to_date(date, 'YYYYMMDD') >= '2026-04-01'
  and to_date(date, 'YYYYMMDD') <  '2026-05-01'
group by 1
order by revenue desc;
```
Expected per the PDF: a Total of revenue `73808` / sessions `15682`, and per-channel rows close to the "PDF reference" table (Direct ~£12,620, Organic Search ~£13,686, Paid Search ~£8,519, Paid Social ~£4,954, Email / CRM ~£11,429, Referral / Affiliates ~£2,369, Other ~£20,231). If the Total revenue is far from `73808`, confirm the channel-grouping report is the right Bronze table and that the `case` folds every raw `sessiondefaultchannelgrouping` value into a display channel (run the query without the `case`, grouped on the raw column, to list the distinct raw values).

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds a new GA4 Bronze source table (`traffic_acquisition_session_default_channel_grouping_report`) and two new dbt models (`stg_google_analytics__channel_sessions`, `fct_ga_channel_sessions`); if `CLAUDE.md` enumerates GA4 models or Gold facts, add the new fact there.
