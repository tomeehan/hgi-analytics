# 009: Top converting sources by RPS

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-009-top_converting_sources_by_rps`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-009-top_converting_sources_by_rps`.
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
- Page 13, section "IS CLINICAL, Traffic, conversion, PR, customer mix, AOV", panel "2B. TOP CONVERTING (RPS)".
- April 2026 values (iS Clinical). The table is the top GA4 source/medium rows ranked by RPS (revenue per session), columns source/medium, RPS, CVR, transactions:

  | source / medium | RPS | CVR | trans |
  |---|---|---|---|
  | `fb / paid` | £14.02 | 12.2% | 12 |
  | `quizify / quiz` | £12.94 | 6.2% | 9 |
  | `isclinical.ie / referral` | £8.13 | 4.0% | 2 |
  | `Klaviyo / email` | £8.21 | 6.0% | 83 |
  | `ig / paid` | £8.00 | 4.1% | 12 |
  | `bing / cpc` | £6.09 | 5.0% | 3 |
  | `google / cpc` | £5.31 | 5.0% | 128 |
  | `(direct) / (none)` | £4.84 | 3.0% | 77 |

  The RPS column is not strictly monotonic in the PDF (`Klaviyo / email` at £8.21 sits below `isclinical.ie / referral` at £8.13). Treat the eight rows as the PDF's curated shortlist and the per row RPS / CVR / transactions values as authoritative; do not re-derive the ordering. The headline RPS for the whole brand is £4.71 (page 13 KPI strip, built by ticket 007), so this table surfaces the above-average converters.

## Metric definition
- A table of the top GA4 source/medium combinations for iS Clinical, ranked by **RPS** (revenue per session). For each source/medium it shows:
  - **RPS** = GA4 attributed revenue / GA4 sessions for that source/medium.
  - **CVR** = GA4 transactions / GA4 sessions for that source/medium, expressed as a percentage.
  - **transactions** = GA4 ecommerce purchase transactions attributed to that source/medium.
- Source of truth chain per the PDF appendix: **GA4** (Google Analytics). The page header marks the whole "Traffic, conversion, PR, customer mix, AOV" page as GA4-sourced, except panels 4 and 5 which are Shopify. This panel (2B) is GA4. Not Shopify, Meta, Google Ads or Klaviyo. Note `Klaviyo / email` here is a GA4 *source/medium* label (how GA4 classifies email click traffic), not a Klaviyo-sourced number.
- Filter behaviour: the table is scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the table must show the April source/medium rows above.

## Data dependencies
- Bronze source needed: `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` (the `TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT` stream) , status **Live** per generator section (c). No Shopify sync-gap note applies (this is a GA4-sourced tile, not a Shopify-sourced one).
- Silver and Gold models that already cover this:
  - `dbt/models/silver/stg_google_analytics__sessions.sql` , **partial fit only.** It reads `traffic_acquisition_session_source_medium_report` but `group by 1, 2` collapses to `session_date` + `store_id`, **dropping the `SESSIONSOURCE` / `SESSIONMEDIUM` columns**. As written it cannot produce a per source/medium table. The source columns exist in Bronze (`SESSIONSOURCE`, `SESSIONMEDIUM`, `SESSIONS`, `TOTALREVENUE`, `EVENTCOUNT`), they just are not carried through.
  - `dbt/models/silver/stg_google_analytics__transactions.sql` , reads `events_report` filtered to `eventname = 'purchase'`. **`events_report` has no source/medium dimension** (verified: its columns are `DATE`, `EVENTNAME`, `EVENTCOUNT`, `TOTALUSERS`, `TOTALREVENUE`, `EVENTCOUNTPERUSER`). So transactions cannot be split by source/medium from this model.
  - `dbt/models/gold/fct_ga_sessions.sql` , a pass-through `select *` over `stg_google_analytics__sessions`, so it inherits the same date-grain limitation.
- **Known data gap (GA4 transactions per source/medium, prerequisite).** The PDF's `trans` column is GA4's ecommerce **transactions** metric split by source/medium (its values 12 / 9 / 2 / 83 / 12 / 3 / 128 / 77 match the page-12 channel-attribution `TRANS` column, not a raw event count). The only source/medium-dimensioned Bronze stream we have, `TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT`, carries `EVENTCOUNT` (the count of **all** events, e.g. 32,677 for `google / cpc`), **not** a `transactions` / `ecommercePurchases` metric. No current GA4 Bronze stream gives transactions broken down by source/medium. To reproduce the PDF's CVR and transactions columns exactly, the Airbyte GA4 connection must add the GA4 `transactions` (or `ecommercePurchases`) metric to the `traffic_acquisition_session_source_medium_report` custom report (or add a new custom report keyed on source/medium that includes it).
  - **Prerequisite:** a separate data-engineering ticket must add the GA4 `transactions` metric to the source/medium custom report in the iS Clinical GA4 Airbyte connection. If no such ticket exists on Basecamp, create one and link it from this card. Document the connection change in `airbyte/README.md`. Until that lands, the table can ship with RPS and revenue correct but CVR/transactions either omitted or approximated, and the closing Basecamp comment must state the gap.

## dbt work
This ticket needs dbt changes. The current `stg_google_analytics__sessions` is date-grain and cannot back a per source/medium table.

- **Modify `dbt/models/silver/stg_google_analytics__sessions.sql`** to carry the source/medium dimension. Add `sessionsource` and `sessionmedium` to the `select` and to the `group by` in the `isclinical` CTE, and project a normalised `source_medium` label, for example `lower(trim(sessionsource)) || ' / ' || lower(trim(sessionmedium)) as source_medium`. Keep the existing `session_date`, `order_month`, `store_id`, `sessions`, `engaged_sessions`, `total_revenue` columns. This is additive: the date-grain consumers (ticket 007's traffic/conversion KPI strip) still aggregate over the new grain, so re-verify ticket 007's totals do not move after the change.
- **Decide where the table aggregation lives.** Either add a Gold model `dbt/models/gold/fct_ga_source_medium.sql` aggregating `stg_google_analytics__sessions` to `store_id` + `order_month` + `source_medium` (summing `sessions`, `total_revenue`), or surface the new grain on `fct_ga_sessions`. A dedicated Gold model is cleaner because the existing `fct_ga_sessions` is consumed at date grain by ticket 007. Expose the metrics `total_sessions` (`sum`), `total_revenue` (`sum`, `format: gbp`), and dimensions `source_medium`, `order_month`, `order_month_label`.
- **RPS and CVR are derived ratios.** RPS = revenue / sessions, CVR = transactions / sessions. Implement RPS as a Lightdash table calculation over the `total_revenue` and `total_sessions` metrics (revenue ÷ sessions), or as a non-additive metric. Do **not** pre-divide per row in the model (ratios do not sum). CVR additionally needs the transactions count: it is **blocked on the prerequisite** above. Until GA4 transactions per source/medium are ingested, ship RPS + revenue + sessions and either omit CVR/transactions or render them with a "not yet available" note.
- **Tests to add:** on the new/modified model, `not_null` on `store_id`, `order_month`, `source_medium`; if a Gold model is added, a `unique` test on the composite key (`store_id` + `order_month` + `source_medium`, via `dbt_utils.unique_combination_of_columns`); `dbt_utils.accepted_range` (`min_value: 0`) on `total_sessions` and `total_revenue`.
- Run `cd dbt && dbt build --select stg_google_analytics__sessions+` and confirm all tests pass, including the downstream `fct_ga_sessions` and ticket 007's consumers.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard in the traffic/conversion area, mirroring the PDF page-13 layout: directly after the traffic/conversion KPI strip (ticket 007) and the "Top GA4 traffic sources by sessions" table (ticket 008). On the PDF, panel 2A (top traffic sources by sessions) is left and panel 2B (top converting by RPS) is right, so place this table immediately after ticket 008's table.
- Create `lightdash/charts/isclinical-top-converting-sources-by-rps.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing chart that already fits and adapt it instead, in particular ticket 008's "top traffic sources by sessions" table chart if it has already landed, since both are GA4 source/medium tables and differ only in columns/ordering.
  - The chart is a table on the new GA4 source/medium explore (`fct_ga_source_medium`, or the new grain on `fct_ga_sessions`), with `source_medium` as the row dimension and a descending sort on the RPS table calculation.
  - Columns, in PDF order: `source / medium`, `RPS`, `CVR`, `transactions`. Add RPS (and CVR if the prerequisite has landed) as table calculations: `RPS = total_revenue / total_sessions`, `CVR = total_transactions / total_sessions`. Limit to the top 8 rows by RPS to mirror the PDF shortlist.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 13 (IS CLINICAL, Traffic, conversion, PR, customer mix, AOV)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. The new GA4 explore **must** expose a matching `order_month_label` dimension (`to_char(order_month, 'YYYY-MM')`) so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto the explore's `order_month_label` field via `tileTargets` in `kpi-report.yml`. Confirm `order_month_label` is present on the explore before editing the YAML (the existing `fct_ga_sessions` carries `order_month`; check it also exposes `order_month_label`, and add it if not).

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert the rows and per row RPS match the April 2026 iS Clinical values in the "PDF reference" section above. CVR and transactions match only if the prerequisite GA4-transactions-per-source/medium ticket has landed; if it has not, those two columns are expected to be absent or approximate, which is an accepted known gap, not a merge blocker.
- If RPS or the source/medium rows do not match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or the known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`).

RPS, sessions and revenue per source/medium (these reproduce the PDF's RPS column):
```sql
select
    lower(trim(sessionsource)) || ' / ' || lower(trim(sessionmedium)) as source_medium,
    sum(sessions)                                          as sessions,
    sum(totalrevenue)                                      as revenue,
    round(sum(totalrevenue) / nullif(sum(sessions), 0), 2) as rps
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT
where to_date(date, 'YYYYMMDD') between '2026-04-01' and '2026-04-30'
group by 1
order by rps desc;
```
Expected per the PDF (RPS): `fb / paid` £14.02, `quizify / quiz` £12.94, `Klaviyo / email` £8.21, `isclinical.ie / referral` £8.13, `ig / paid` £8.00, `bing / cpc` £6.09, `google / cpc` £5.31, `(direct) / (none)` £4.84.

CVR / transactions check (this is the gap). The `TRANS` column the PDF shows is GA4's ecommerce `transactions` metric per source/medium, which is **not** ingested. The only count this stream carries is `EVENTCOUNT`, the count of all events, which does **not** equal the PDF's transactions:
```sql
select
    lower(trim(sessionsource)) || ' / ' || lower(trim(sessionmedium)) as source_medium,
    sum(sessions)   as sessions,
    sum(eventcount) as eventcount
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT
where to_date(date, 'YYYYMMDD') between '2026-04-01' and '2026-04-30'
group by 1
order by sessions desc;
```
If `eventcount` is in the tens of thousands per source (e.g. ~32,677 for `google / cpc`) it confirms it is not the transactions metric: the PDF's `google / cpc` transactions value is 128. This is the documented prerequisite gap, not a model defect.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). Adding a Gold model `fct_ga_source_medium` and changing `stg_google_analytics__sessions` to a source/medium grain is a structural change worth a one-line note in the Gold-models list. If the prerequisite GA4-transactions ticket is completed alongside this one, record the resolution and the Airbyte connection change in `CLAUDE.md` and `airbyte/README.md`.
