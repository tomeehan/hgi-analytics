# 008: Top traffic sources by sessions

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-008-top_traffic_sources_by_sessions`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-008-top_traffic_sources_by_sessions`.
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
- Page 13, section "IS CLINICAL, Traffic, conversion, PR, customer mix, AOV" (panel "2A. TOP TRAFFIC SOURCES BY SESSIONS, GA4").
- April 2026 value (iS Clinical): the eight-row source/medium table, ranked by sessions:

  | source / medium | sessions | revenue | trans |
  |---|---|---|---|
  | google / organic | 2,855 | £13,536 | 98 |
  | (not set) | 2,633 | £10,630 | 86 |
  | (direct) / (none) | 2,610 | £12,620 | 77 |
  | google / cpc | 2,578 | £13,692 | 128 |
  | facebook / cpc | 1,687 | £1,719 | 17 |
  | Klaviyo / email | 1,392 | £11,429 | 83 |
  | webgains / affiliate | 676 | £1,418 | 8 |
  | ig / paid | 292 | £2,335 | 12 |

  Verified against the PDF page 13. The table title in the PDF prints `(not set)` as the second row's `source / medium` label; in the underlying Bronze data the medium for that row is also `(not set)`, so the row key is `(not set) / (not set)` (display label can be shortened to `(not set)`).

## Metric definition
- A ranked table of GA4 traffic-acquisition source/medium combinations for iS Clinical, ordered by `sessions` descending, showing the top rows. Columns: `source / medium`, `sessions`, `revenue`, `transactions`.
- `sessions` is the GA4 session count for that source/medium. `revenue` is GA4 `totalRevenue` attributed to that source/medium. `transactions` is the GA4 purchase-event count for that source/medium.
- Source of truth chain per the PDF appendix: **GA4** (the `traffic_acquisition_session_source_medium_report` traffic-acquisition report). Not Shopify, Meta, Google Ads or Klaviyo. The PDF panel header marks this panel `GA4`.
- Filter behaviour: the tile is a table scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the table must show the April 2026 source/medium rows, ranked by sessions.

## Data dependencies
- Bronze source needed: `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL`, table `traffic_acquisition_session_source_medium_report`, status **Live** per generator section (c) ("10 reports loaded, including source/medium"). No Shopify sync-gap note applies (this is a GA4-sourced tile, not a Shopify-sourced one).
- Silver and Gold models that already cover this:
  - `dbt/models/silver/stg_google_analytics__sessions.sql` exists, but it **aggregates the source/medium report away**: it groups by `session_date` and `store_id` only, dropping `sessionsource` / `sessionmedium`, and emits `sessions`, `engaged_sessions`, `total_revenue`. It does **not** carry source/medium and does **not** carry a transaction count.
  - `dbt/models/gold/fct_ga_sessions.sql` is a pass-through `select *` over `stg_google_analytics__sessions` (date-grain, no source/medium).
  - `dbt/models/silver/stg_google_analytics__transactions.sql` carries a daily purchase-event count from `events_report`, but at `session_date` grain only (no source/medium dimension).
- New Silver and Gold models or columns required: **yes.** No existing model surfaces GA4 source/medium rows, so this tile needs a new model. See "dbt work".

## dbt work
The current `stg_google_analytics__sessions` collapses the source/medium dimension, so a new model is required. Add a source/medium-grain GA4 model:

- **New Silver model `dbt/models/silver/stg_google_analytics__source_medium.sql`**, selects from `source('bronze_google_analytics_isclinical', 'traffic_acquisition_session_source_medium_report')`, grouped by `session_date`, `store_id`, `sessionsource`, `sessionmedium`. Emit columns: `session_date`, `order_month` (`date_trunc('month', session_date)::date`), `store_id` (`'isclinical'`), `source_medium` (`sessionsource || ' / ' || sessionmedium`), `sessions` (`sum(sessions)`), `revenue` (`sum(totalrevenue)`), `transactions`. Mirror the `where date is not null` and union-CTE pattern of the existing `stg_google_analytics__sessions` so a future brand is a one-CTE add.
- **New Gold model `dbt/models/gold/fct_ga_source_medium.sql`**, a `select *` pass-through over the new Silver model (mirrors how `fct_ga_sessions` wraps `stg_google_analytics__sessions`), materialised as a table. This is the explore the tile reads from.
- **Transactions column caveat.** The PDF `trans` column is the GA4 purchase-event count per source/medium. The `traffic_acquisition_session_source_medium_report` Bronze table has an `eventcount` column, but that is *total* events per session, not the purchase-event count, so it cannot be used directly for `transactions`. The clean source of a purchase count per source/medium is a GA4 events report that carries both `eventname` and the source/medium dimension. Confirm whether `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` has such a stream (rule 3): if it does, build `transactions` from it (`eventname = 'purchase'`, grouped by source/medium and date); if it does not, ship the table with `source_medium`, `sessions` and `revenue` only, note the `transactions` gap explicitly, and raise a prerequisite data-engineering ticket to add a source/medium-dimensioned GA4 conversions report to the Airbyte connection. The PDF figures stay authoritative; the `transactions` column reads blank until that report lands.
- **Schema entries.** Add both new models to `dbt/models/silver/_schema.yml` and `dbt/models/gold/_schema.yml`. Expose `order_month` and an `order_month_label` (`to_char(order_month, 'YYYY-MM')`) additional dimension on the Gold model so the dashboard Month filter cross-applies (see "Lightdash work").
- **Tests.** On the Gold model: `not_null` on `store_id`, `order_month`, `source_medium`; a `dbt_utils.unique_combination_of_columns` test on (`session_date`, `store_id`, `source_medium`) as the natural key; `dbt_utils.accepted_range` (`min_value: 0`) on `sessions`, `revenue` and (if built) `transactions`.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard under the "Traffic, conversion, PR, customer mix, AOV" section (PDF page 13), directly below the traffic & conversion KPI strip built by ticket 007, in the left-hand column (the PDF places panel 2A on the left, panel 2B "Top converting sources by RPS", built by ticket 009, on the right).
- Create `lightdash/charts/isclinical-top-traffic-sources.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing table chart to adapt; there is no existing GA4 source/medium table chart, so adapt the nearest table chart for structure.
  - The chart is a **table** on the new `fct_ga_source_medium` explore. Dimension: `source_medium`. Metrics: `sessions` (sum), `revenue` (sum, `format: gbp`), `transactions` (sum). Sort by `sessions` descending. Limit the table to the top 8 rows to mirror the PDF panel.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 13 (IS CLINICAL, Traffic, conversion, PR, customer mix, AOV)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. The new `fct_ga_source_medium` explore **must** expose a matching `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`) so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_ga_source_medium_order_month_label` via `tileTargets` in `kpi-report.yml`. Confirm `order_month` / `order_month_label` are present on the explore before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert the rows match the April 2026 iS Clinical source/medium table in the "PDF reference" section above: eight rows, ranked by sessions, with `google / organic` first at ~2,855 sessions / £13,536 / 98 transactions through to `ig / paid` last.
- If it does not match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or a known data-availability gap from section (c), and note the cause in the ticket. Small per-row drift (sessions and revenue a little low) is expected: GA4 ingestion lands incrementally, so the live Bronze totals can sit slightly below the PDF snapshot. If only the `transactions` column is blank, that is the documented purchase-count gap from the "dbt work" section, not a tile defect, and merge is still acceptable provided the closing Basecamp comment names the gap and links the prerequisite ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`):
```sql
select
    sessionsource || ' / ' || sessionmedium as source_medium,
    sum(sessions)                           as sessions,
    round(sum(totalrevenue))                as revenue
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT
where to_date(date, 'YYYYMMDD') >= '2026-04-01'
  and to_date(date, 'YYYYMMDD') <  '2026-05-01'
group by 1
order by sessions desc
limit 8;
```
Expected per the PDF: `google / organic` ~2,855 sessions / £13,536, `(not set) / (not set)` ~2,633 / £10,630, `(direct) / (none)` ~2,610 / £12,620, `google / cpc` ~2,578 / £13,692, `facebook / cpc` ~1,687 / £1,719, `Klaviyo / email` ~1,392 / £11,429, `webgains / affiliate` ~676 / £1,418, `ig / paid` ~292 / £2,335. Once the new Gold model exists, run the same check against it:
```sql
select source_medium, sum(sessions) as sessions, round(sum(revenue)) as revenue
from HGI.GOLD.FCT_GA_SOURCE_MEDIUM
where store_id = 'isclinical'
  and order_month = '2026-04-01'
group by 1
order by sessions desc
limit 8;
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds two new dbt models (`stg_google_analytics__source_medium`, `fct_ga_source_medium`); if that materially changes the Gold model inventory, update the relevant list in `CLAUDE.md` in the same PR.
