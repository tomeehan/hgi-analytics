# 007: Traffic & conversion KPI strip

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-007-traffic_conversion_kpi_strip`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-007-traffic_conversion_kpi_strip`.
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
- Page 13, section "IS CLINICAL, Traffic, conversion, PR, customer mix, AOV".
- April 2026 values (iS Clinical), the five big numbers in the KPI strip at the top of the page:
  - Sessions: **15,682**
  - Users: **13,300**
  - CVR (GA): **3.53%**
  - RPS: **£4.71**
  - AOV (GA-derived): **£133.23**

This is the GA4 traffic and conversion strip. It is GA4-sourced end to end (the page header is tagged "GA4"), distinct from the Shopify source-of-truth headline KPIs on page 12. The "vs Mar" deltas printed under each number (sessions +9.0%, CVR +0.68pp, RPS +£1.20) are not part of this tile, they are reproduced separately if a month-over-month tile is ever added.

## Metric definition
- A KPI strip of five GA4-derived big numbers describing iS Clinical website traffic and conversion for the month:
  - **Sessions** = total GA4 sessions.
  - **Users** = total GA4 users (distinct users, GA4 `totalUsers`).
  - **CVR (GA)** = conversion rate = GA4 transactions / GA4 sessions, expressed as a percentage. PDF: 554 / 15,682 = 3.53%.
  - **RPS** = revenue per session = GA-attributed revenue / GA4 sessions. PDF: £73,808 / 15,682 = £4.71.
  - **AOV (GA-derived)** = average order value derived from GA = GA-attributed revenue / GA4 transactions. PDF: £73,808 / 554 = £133.23. This is the GA-derived AOV, deliberately different from the Shopify source-of-truth AOV of £134.45 on page 12 (ticket 005), because GA's transaction count (554) and revenue (£73,808) differ from Shopify's order count (1,075) and revenue (£144,532).
- Source of truth chain per the PDF appendix: **GA4** end to end. Sessions and users come from GA4's website-overview report; transactions come from GA4 `purchase` events; revenue is GA-attributed purchase revenue. Not Shopify, Meta, Google Ads or Klaviyo.
- Filter behaviour: every number in the strip is scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the five numbers must read 15,682 sessions, 13,300 users, 3.53% CVR, £4.71 RPS, £133.23 AOV (the PDF's iS Clinical figures, subject to the GA-window caveat in "Data dependencies").

## Data dependencies
- Bronze sources needed:
  - `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT` (sessions, GA-attributed revenue), status **Live** per generator section (c).
  - `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.WEBSITE_OVERVIEW` (users, via the `TOTALUSERS` column), status **Live** per generator section (c) ("website overview" is one of the 10 GA4 reports loaded). This Bronze table is **not yet wired into any Silver/Gold model**, see "dbt work".
  - `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.EVENTS_REPORT` (transactions, `purchase` event count), status **Live**.
- No Shopify sync-gap note applies: this is a GA4-sourced tile, not a Shopify-sourced one.
- Silver and Gold models that already cover part of this:
  - `dbt/models/silver/stg_google_analytics__sessions.sql`: Silver staging for sessions, engaged sessions, GA-attributed revenue, with `order_month`.
  - `dbt/models/gold/fct_ga_sessions.sql`: Gold fact, currently `select * from stg_google_analytics__sessions`. Exposes the `sessions` column (metric `total_ga_sessions`), `total_revenue` (metric `ga_total_revenue`), `order_month` and the `order_month_label` additional dimension. **It has no `users` column and no `transactions` column today.**
  - `dbt/models/silver/stg_google_analytics__transactions.sql`: Silver staging for GA4 transactions (`purchase` event count), with `order_month`. This model already exists but is **not selected into any Gold model**.
- New Silver or Gold models or columns required: yes, see "dbt work". `users` is not staged anywhere yet, and neither `users` nor `transactions` reaches Gold. CVR, RPS and AOV are derived ratios and are not stored as columns: they are computed in Lightdash as metric-on-metric (or table-calculation) divisions.
- **GA reporting-window caveat.** Bronze GA4 numbers do not land exactly on the PDF. Querying Snowflake on 2026-05-20: `WEBSITE_OVERVIEW` April 2026 totals are 15,647 sessions and 13,829 users, and `TRAFFIC_ACQUISITION_SESSION_SOURCE_MEDIUM_REPORT` sums to 15,638 sessions, against the PDF's 15,682 sessions and 13,300 users. GA4 reports keep re-processing for several days after the month closes and the two GA4 reports disagree slightly on sessions. This is a known GA data-latency / report-definition gap, not a model defect. The PDF figure is authoritative; the live tile will read slightly differently. Note the live values explicitly in the Basecamp closing comment.

## dbt work
The five-number strip needs `sessions`, `users`, `transactions` and GA-attributed `revenue` all reachable from one explore so a single tile (or one chart per number, see "Lightdash work") can read them and derive CVR / RPS / AOV. `fct_ga_sessions` already carries `sessions` and `total_revenue` but is missing `users` and `transactions`.

1. **New Silver model `dbt/models/silver/stg_google_analytics__users.sql`.** Stage daily users from `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.WEBSITE_OVERVIEW`: `to_date(date,'YYYYMMDD') as session_date`, `'isclinical' as store_id`, `sum(totalusers) as users`, plus `date_trunc('month', session_date)::date as order_month`. Follow the exact CTE-per-brand shape of `stg_google_analytics__sessions.sql` (a single `isclinical` CTE today, `unioned` CTE for future brands).
2. **Modify `dbt/models/gold/fct_ga_sessions.sql`.** Replace the bare `select *` with a join that brings `users` (from the new `stg_google_analytics__users`) and `transactions` (from the existing `stg_google_analytics__transactions`) onto the daily sessions grain, joining on `(session_date, store_id)`. Use left joins from sessions so a day with sessions but no users / transactions row still appears, and `coalesce(... , 0)` the joined-in counts.
3. **Modify `dbt/models/gold/_schema.yml`** (the `fct_ga_sessions` block):
   - Add a `users` column with a `total_ga_users` metric (`type: sum`, `label: "GA Users"`, `round: 0`).
   - Add a `transactions` column with a `total_ga_transactions` metric (`type: sum`, `label: "GA Transactions"`, `round: 0`).
   - Add three derived metrics for the strip's ratios. Either as `type: number` metrics on the explore (e.g. `ga_conversion_rate` = `${total_ga_transactions} / nullif(${total_ga_sessions}, 0)`, `ga_revenue_per_session` = `${ga_total_revenue} / nullif(${total_ga_sessions}, 0)`, `ga_aov` = `${ga_total_revenue} / nullif(${total_ga_transactions}, 0)`), or leave them as Lightdash table calculations in the chart YAML if the explore-level `type: number` metric is awkward. State which approach the executor used. CVR is a ratio in the 0 to 1 range surfaced as a percentage: set `format: percent` on `ga_conversion_rate`; set `format: gbp` on `ga_revenue_per_session` and `ga_aov`.
- Tests to add: `not_null` on `session_date` and `store_id` already exist on `fct_ga_sessions`. Add `dbt_utils.accepted_range` (`min_value: 0`) on the new `users` and `transactions` columns. Keep the existing `not_null` on `order_month`. No new key needs a `unique` test (the grain is unchanged: one row per `session_date` × `store_id`).
- Run `cd dbt && dbt build --select stg_google_analytics__users+ fct_ga_sessions+` and confirm all tests pass.

## Lightdash work
- Tile type: a **KPI strip** is a row of big numbers. Per generator rule 5, one PDF visual unit is one tile and one ticket, but Lightdash has no native multi-number tile: a "strip" is built as **five adjacent big-number tiles laid out in one row**. Create one big-number chart per number and place all five side by side, under a markdown / section heading "Traffic & conversion (GA4)" that mirrors the PDF page-13 strip. This row sits after the page-12 Revenue & Channel Attribution tiles (ticket 005 / 006) and before the page-13 traffic-source tables (tickets 008 / 009), matching PDF reading order.
- Charts to create (one file per tile, all on the `fct_ga_sessions` explore):
  - `lightdash/charts/isclinical-ga-sessions.yml`: big number, metric `total_ga_sessions`.
  - `lightdash/charts/isclinical-ga-users.yml`: big number, metric `total_ga_users`.
  - `lightdash/charts/isclinical-ga-cvr.yml`: big number, metric `ga_conversion_rate` (percent format).
  - `lightdash/charts/isclinical-ga-rps.yml`: big number, metric `ga_revenue_per_session` (gbp format).
  - `lightdash/charts/isclinical-ga-aov.yml`: big number, metric `ga_aov` (gbp format).
  - Before creating these, check `lightdash/charts/` for an existing big-number chart to adapt: `combined-shopify-revenue.yml` and `combined-meta-spend.yml` (or whatever tickets 001 to 005 left behind, e.g. an `isclinical-*` big-number chart) are good templates. If ticket 005's revenue-and-channel-attribution strip already created a reusable big-number pattern on a GA explore, adapt that.
- Update `lightdash/dashboards/kpi-report.yml` to add all five tiles in one row.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 13 (IS CLINICAL, Traffic, conversion, PR, customer mix, AOV)`.
- How the tiles pick up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. `fct_ga_sessions` exposes a matching `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`), so Lightdash cross-applies the filter by field name. Cross-apply the Month filter onto `fct_ga_sessions_order_month_label` via `tileTargets` in `kpi-report.yml` for each of the five tiles. Confirm `order_month_label` is present on the `fct_ga_sessions` explore before editing the YAML (it is, see `dbt/models/gold/_schema.yml`).

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF numbers:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read all five tile values.
- Assert they equal the April 2026 iS Clinical values stated in the "PDF reference" section above (15,682 sessions, 13,300 users, 3.53% CVR, £4.71 RPS, £133.23 AOV).
- If they do not match, do not merge until you have established the cause: reproduce the numbers with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or the known GA reporting-window gap from "Data dependencies". The expected outcome is a small discrepancy on sessions and users (Snowflake holds ~15,640 sessions and ~13,830 users for April vs the PDF's 15,682 and 13,300) because GA4 reports keep re-processing after month close. That is acceptable to merge: the tiles are correctly wired and read the live GA4 numbers. The Basecamp closing comment must state the live values, name the GA-window gap, and confirm the derivation logic (CVR = transactions / sessions, RPS = revenue / sessions, AOV = revenue / transactions) is correct.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`). After the dbt work lands, the whole strip reproduces from `fct_ga_sessions`:
```sql
select
    sum(sessions)                                as sessions,
    sum(users)                                   as users,
    sum(transactions)                            as transactions,
    sum(total_revenue)                           as ga_revenue,
    sum(transactions) / nullif(sum(sessions), 0) as cvr,
    sum(total_revenue) / nullif(sum(sessions), 0)      as rps,
    sum(total_revenue) / nullif(sum(transactions), 0)  as aov
from HGI.GOLD.FCT_GA_SESSIONS
where store_id = 'isclinical'
  and order_month = '2026-04-01';
```
Expected per the PDF: 15,682 sessions, 13,300 users, 554 transactions, £73,808 revenue, CVR 0.0353, RPS 4.71, AOV 133.23. The GA-window caveat means sessions and users will read slightly different (Snowflake: ~15,640 sessions, ~13,830 users). To check the raw Bronze before the dbt models land:
```sql
-- sessions + users from WEBSITE_OVERVIEW
select sum(sessions) as sessions, sum(totalusers) as users
from HGI.BRONZE_GOOGLE_ANALYTICS_ISCLINICAL.WEBSITE_OVERVIEW
where to_date(date, 'YYYYMMDD') >= '2026-04-01'
  and to_date(date, 'YYYYMMDD') <  '2026-05-01';

-- transactions from the purchase event count
select sum(transactions) as transactions
from HGI.SILVER.STG_GOOGLE_ANALYTICS__TRANSACTIONS
where store_id = 'isclinical'
  and order_month = '2026-04-01';
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket adds a new Silver model (`stg_google_analytics__users`), wires the GA4 `WEBSITE_OVERVIEW` Bronze table into the pipeline for the first time, and broadens `fct_ga_sessions` from sessions-only to a full GA4 traffic-and-conversion fact (sessions, users, transactions, revenue, plus derived CVR / RPS / AOV metrics). If the architecture doc or `CLAUDE.md` describes `fct_ga_sessions` narrowly as a sessions fact, update that description so the doc stays accurate.
