# 010: PR & media highlights

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-010-pr_media_highlights`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-010-pr_media_highlights`.
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
- Page 14, section "IS CLINICAL, Traffic, conversion, PR, customer mix, AOV, panel 3. PR & MEDIA HIGHLIGHTS (GA4 referrers)". (The section heading "Traffic, conversion, PR, customer mix, AOV" sits on page 13; page 14 is its continuation and carries the PR & media highlights panel top-left, with the customer mix / AOV split panel to its right.)
- April 2026 value (iS Clinical): the panel is a small table, **3 rows**:

  | Referrer | Sessions | Revenue | Trans |
  |---|---|---|---|
  | `quizify / quiz (Quizify quiz)` | 146 | £1,890 | 9 |
  | `isclinical.ie / referral` | 50 | £407 | 2 |
  | `chatgpt.com` | 60 | £0 | 0 |

  Footnote on the panel: *"No standalone PR placement detected above 100 sessions."*

## Metric definition
- Plain English: the top GA4 referral / off-site traffic sources for iS Clinical in the month, the closest proxy the report has for earned PR and media coverage. Each row is one referrer (a GA4 source, optionally qualified by medium) with its sessions, GA-attributed revenue and transactions. The panel deliberately surfaces non-paid, non-search referrers (a quiz partner, a sibling-brand domain, an AI assistant) rather than `google / organic` or paid channels, which are covered by the traffic-sources panels in tickets 008 and 009.
- Source of truth chain per the PDF appendix: **GA4** only. The session and revenue figures come from the GA4 traffic-acquisition source/medium report (`BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT`). Not Shopify, Meta, Google Ads or Klaviyo.
- Filter behaviour: the tile is a **table** scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the table must show the three PR/media referrer rows above.

## Data dependencies
- Bronze source needed: `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` (stream `traffic_acquisition_session_source_medium_report`), status **Live** per generator section (c): "GA4 (Google Analytics) iS Clinical: Live, 10 reports loaded". The Shopify sync-gap note does **not** apply (this is a GA4-sourced tile, not a Shopify-sourced one).
- Silver and Gold models that already cover this:
  - `dbt/models/silver/stg_google_analytics__sessions.sql` and `dbt/models/gold/fct_ga_sessions.sql`: these exist, but they **collapse** the source/medium dimension. `stg_google_analytics__sessions` does `group by session_date, store_id` and never selects `sessionsource` / `sessionmedium`, so `fct_ga_sessions` has one row per `session_date` x `store_id` and **cannot** surface per-referrer rows. There is no model anywhere under `dbt/models/` that exposes GA4 source/medium as a dimension (verified: `_sources.yml` declares the Bronze stream, but no Silver/Gold model keeps the columns).
  - `dbt/models/silver/stg_google_analytics__transactions.sql` exists but is keyed on transactions, not source/medium, and the source/medium Bronze report does **not** carry a transactions column (verified: it has `SESSIONS`, `TOTALUSERS`, `TOTALREVENUE`, `SESSIONSOURCE`, `SESSIONMEDIUM`, `ENGAGEDSESSIONS`, no transaction count).
- New Silver or Gold models or columns required: **yes.** A new source/medium-grain GA4 model is needed (see "dbt work"). Tickets 008 (top traffic sources by sessions) and 009 (top converting sources by RPS) need the same source/medium-grain model, so build it once and let all three tickets share it. If ticket 008 or 009 has already landed `fct_ga_traffic_sources` (or similar), reuse it here and skip the model creation.
- **Known data gap (referrer reconciliation, note explicitly).** The PDF's `chatgpt.com` row reads **60 sessions / £0 / 0 trans**, but `chatgpt.com` does not reconcile cleanly to the GA4 source/medium report: in `TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT` for April 2026, `sessionsource = 'chatgpt.com'` with `sessionmedium = 'referral'` is **16 sessions**, and `chatgpt.com` across **all** mediums is **76 sessions**. Neither equals 60. The `quizify / quiz` and `isclinical.ie / referral` rows **do** reconcile exactly (146 / £1,890 and 50 / £407). The PDF figure for `chatgpt.com` is a hand-curated value (the report author appears to have de-duplicated or trimmed AI-assistant traffic). The PDF is authoritative for the printed report; the live tile, driven straight off GA4, will show whatever the source/medium report yields for `chatgpt.com` and may not read exactly 60. Note this in the Basecamp closing comment rather than forcing the model to match.

## dbt work
- **Add a new Gold model `dbt/models/gold/fct_ga_traffic_sources.sql`** (and its Silver staging model `dbt/models/silver/stg_google_analytics__traffic_sources.sql`), grain **one row per `session_date` x `store_id` x `source_medium`**, selecting from `source('bronze_google_analytics_isclinical', 'traffic_acquisition_session_source_medium_report')`. Columns:
  - `session_date` (`to_date(date, 'YYYYMMDD')`), `order_month` (`date_trunc('month', session_date)::date`), `store_id` (`'isclinical'`).
  - `session_source` (`SESSIONSOURCE`), `session_medium` (`SESSIONMEDIUM`), and a combined `source_medium` label (`session_source || ' / ' || session_medium`).
  - `sessions` (`sum(SESSIONS)`), `total_revenue` (`sum(TOTALREVENUE)`), `engaged_sessions` (`sum(ENGAGEDSESSIONS)`).
  - Rationale: this is the missing source/medium-grain GA4 model. `stg_google_analytics__sessions` already collapses the dimension, so a sibling staging model that preserves it is the cleanest fix (do not mutate the existing model: ticket 005's GA-attributed-revenue tile and `fct_ga_sessions` depend on its current grain). Follow the manual CTE-per-store union pattern from `stg_google_analytics__sessions` so a future brand drops in cleanly.
  - **Transactions:** the source/medium Bronze report has no transaction count. Two options, pick one and document it: (a) leave `transactions` off the model and have the Lightdash table show Referrer / Sessions / Revenue only (the Trans column from the PDF is then omitted, acceptable, note it); or (b) join the source/medium report to a GA4 e-commerce / conversions report keyed on source/medium if one of the 10 loaded GA4 reports carries transactions at that grain, check `_sources.yml` and the Bronze schema first. Prefer (a) for the first cut unless a transactions-by-source report is readily available.
- Expose, in `dbt/models/gold/_schema.yml` under the new model: an `order_month` dimension with an `order_month_label` additional dimension (`to_char(${TABLE}.order_month, 'YYYY-MM')`), mirroring `fct_ga_sessions` so the dashboard Month filter cross-applies; `store_id` with the standard human-readable `case` rename; `source_medium` as a string dimension; and `sum`-type metrics for `sessions` and `total_revenue` (`format: gbp` on revenue).
- Tests to add: `not_null` on `session_date`, `order_month`, `store_id`, `source_medium`; a `dbt_utils.accepted_range` (`min_value: 0`) range test on `sessions` and `total_revenue`. There is no single-column unique key (the grain is composite); add a `dbt_utils.unique_combination_of_columns` test on `[session_date, store_id, source_medium]` instead.
- If a prior ticket (008 / 009) already created `fct_ga_traffic_sources`, write "no dbt changes needed, model already exists" and reuse it.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard in the traffic / customer-mix area, mirroring the PDF page-14 layout: the PR & media highlights panel is top-left of that page. Place this tile after ticket 009's "Top GA4 converting sources by RPS" table and before ticket 011's "Customer mix & AOV split" tile, so the dashboard row order follows the PDF.
- Create `lightdash/charts/isclinical-pr-media-highlights.yml` (one file per tile). Before creating it, check `lightdash/charts/` for an existing chart that already fits and adapt it: tickets 008 / 009 produce GA4 source/medium tables on the same explore and are the natural templates to copy; if `isclinical-top-traffic-sources.yml` or similar exists, adapt it. Otherwise build a fresh table chart.
  - The chart is a **table** on the new `fct_ga_traffic_sources` explore. Dimension: `source_medium` (the Referrer column). Metrics: `sessions`, `total_revenue` (and `transactions` only if dbt option (b) above was taken).
  - Restrict the table to referral / off-site traffic so it reads as a "PR & media" panel rather than the full traffic mix: add a chart-level filter on `session_medium` (for example `in ('referral', 'quiz')`), sorted by `sessions` descending, and limit the row count so it stays a compact highlights panel (the PDF shows 3 rows). Do not let `google / organic`, `(direct) / (none)` or paid mediums leak in, those belong to tickets 008 / 009.
- Update `lightdash/dashboards/kpi-report.yml` to add the tile.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 14 (IS CLINICAL, Traffic, conversion, PR, customer mix, AOV, panel 3. PR & MEDIA HIGHLIGHTS)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. The new `fct_ga_traffic_sources` explore must expose a matching `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`), exactly as `fct_ga_sessions` does, so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_ga_traffic_sources_order_month_label` via `tileTargets` in `kpi-report.yml`. Confirm `order_month_label` is present on the explore before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile.
- Assert the top two rows match the PDF exactly: `quizify / quiz` at **146 sessions / £1,890** and `isclinical.ie / referral` at **50 sessions / £407**. These reconcile to the source data.
- The `chatgpt.com` row will not necessarily read **60 sessions** (see the "Known data gap" note: GA4 yields 16 sessions for `chatgpt.com / referral` and 76 across all mediums in April, neither is 60). This is expected. The PDF's 60 is a curated figure. If the top two rows match, the tile is correct; merge is acceptable. Note the `chatgpt.com` discrepancy in the Basecamp closing comment.
- If the top two rows do **not** match, do not merge: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`):
```sql
select
    sessionsource || ' / ' || sessionmedium as referrer,
    sum(sessions)                           as sessions,
    sum(totalrevenue)                       as revenue
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT
where to_date(date, 'YYYYMMDD') >= '2026-04-01'
  and to_date(date, 'YYYYMMDD') <  '2026-05-01'
  and sessionmedium in ('referral', 'quiz')
group by 1
order by sessions desc
limit 10;
```
Expected per the PDF: `quizify / quiz` at `146` sessions / `~1890` revenue, `isclinical.ie / referral` at `50` sessions / `~407` revenue. The `chatgpt.com` referrer reads `16` sessions for medium `referral` and `76` across all mediums, not the PDF's `60` (the curated-figure discrepancy described in "Data dependencies"). Once `fct_ga_traffic_sources` exists, re-run the same aggregation against `HGI.GOLD.FCT_GA_TRAFFIC_SOURCES` filtered to `store_id = 'isclinical'` and `order_month = '2026-04-01'` to confirm the model reproduces the Bronze numbers.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds a new Gold model (`fct_ga_traffic_sources`) at a new grain (GA4 source/medium); add it to the Gold model list in `CLAUDE.md` under the "Gold" bullet so the model inventory stays accurate. If tickets 008 / 009 already created the model and recorded it, no `CLAUDE.md` change is needed.
