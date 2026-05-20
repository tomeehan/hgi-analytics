# 005: Revenue & Channel Attribution KPI strip

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-005-revenue_channel_attribution_kpis`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-005-revenue_channel_attribution_kpis`.
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
- Page 12, section "IS CLINICAL, 1. REVENUE & CHANNEL ATTRIBUTION".
- April 2026 values (iS Clinical), the four big numbers in the headline KPI strip at the top of the page:
  - **Total Revenue (Shopify): £144,532** (sub-label "1,075 orders, source of truth").
  - **Revenue (GA4-attributed): £73,808** (sub-label "51.1% of Shopify total").
  - **AOV (Shopify): £134.45** (sub-label "£144,532 / 1,075 orders").
  - **Customer Mix (Shopify): 36% / 64%** (sub-label "385 new / 690 returning orders").

This ticket builds the **KPI strip only**: the row of four big numbers across the top of page 12. The GA4 channel breakdown table lower on the same page (Direct, Organic Search, Paid Search, Paid Social, Email / CRM, Referral / Affiliates, Other, totalling £73,808) is a separate visual unit and is covered by ticket 006 (`channel_breakdown_table`). Per generator rule 5, a KPI strip that shows several numbers in one row on the PDF is one tile and one ticket; this is that one tile.

Note on "largest GA4 channel": the page 12 KPI strip has exactly four boxes (the four listed above) and no "largest channel" box. For reference, the largest single named channel in the channel table is **Organic Search at £13,686 (18.5%)**; the £20,231 "Other" row is a residual bucket (Paid Shopping, Cross-network, Unassigned, Organic Social/Shopping), not a single channel. The channel-level numbers belong to ticket 006, not this strip.

## Metric definition
- **Total Revenue (Shopify):** sum of Shopify order value (`total_price`) for iS Clinical orders placed in the month. The PDF treats Shopify as the source of truth for revenue.
- **Revenue (GA4-attributed):** sum of GA4 purchase-event revenue (`totalRevenue`) for iS Clinical sessions in the month. This is what GA4 attributes across all channels; it is structurally lower than the Shopify figure (51.1% of it in April 2026) because GA4 misses sessions without analytics consent / cross-device journeys.
- **AOV (Shopify):** Shopify total revenue divided by Shopify order count for the month (£144,532 / 1,075 = £134.45). Computed as the `average` of `total_price`.
- **Customer Mix (Shopify):** the new-vs-returning split of Shopify orders, expressed as two percentages. April 2026: 385 new orders (35.8%, rounds to 36%) and 690 returning orders (64.2%, rounds to 64%), out of 1,075 total. New orders are rows where `is_first_order = 1`.
- Source of truth chain per the PDF appendix: **Shopify** for revenue, orders, AOV and customer mix; **GA4** for the GA4-attributed revenue figure. Not Meta, Google Ads or Klaviyo.
- Filter behaviour: every number in the strip is scoped by the dashboard's **Month** filter. With the Month filter on April 2026 the strip must read £144,532 / £73,808 / £134.45 / 36% / 64% (the PDF's iS Clinical figures).

## Data dependencies
- Bronze sources needed:
  - `BRONZE_SHOPIFY_ISCLINICAL` (Total Revenue, AOV, Customer Mix), status **Degraded** per generator section (c). See the sync-gap note below.
  - `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` (GA4-attributed Revenue), status **Live** per generator section (c): 10 GA4 reports loaded, including the traffic-acquisition source/medium report this strip reads from.
- Silver and Gold models that already cover this:
  - `dbt/models/gold/fct_orders.sql`: Shopify orders fact. Exposes the `total_revenue` metric (`sum` of `total_price`, `format: gbp`), the `aov` metric (`average` of `total_price`, `format: gbp`), the `order_count` metric (`count_distinct` of `order_id`), the `new_customer_orders` metric (`sum` of `is_first_order`), and the `order_month` / `order_month_label` dimensions. Confirmed against `dbt/models/gold/_schema.yml`.
  - `dbt/models/gold/fct_ga_sessions.sql`: daily GA4 sessions by `store_id`. Exposes the `ga_total_revenue` metric (`sum` of `total_revenue`, `format: gbp`) and the `order_month` / `order_month_label` dimensions. Confirmed against `dbt/models/gold/_schema.yml`.
- New Silver or Gold models or columns required: **none**. Every metric and dimension this strip needs already exists. The strip is a presentation-only change. (The new-vs-returning split is delivered by `order_count` plus `new_customer_orders` plus a returning-orders metric: see the "dbt work" section, which adds one small metric if a `returning_customer_orders` metric does not already exist.)
- **Known data gap: the iS Clinical Shopify Airbyte sync is degraded.** The iS Clinical Shopify source authenticates with a rotating OAuth token (not a static custom-app token). The token fails mid-sync and Airbyte silently drops scattered records rather than erroring, so Bronze runs roughly **2.6% short** for a full month. For April 2026, Bronze holds **1,047 orders** against the **1,075** stated in the PDF. The three Shopify-derived numbers in this strip (Total Revenue, AOV, Customer Mix) will all read slightly low against the PDF until the sync is fixed. The PDF figures are authoritative. This depends on the "fix iS Clinical Shopify sync" data-engineering ticket (the same prerequisite linked from tickets 001, 002 and 011); if that ticket does not yet exist on Basecamp, create it and link it from this card. The GA4-attributed Revenue number is unaffected (GA4 is Live).

## dbt work
- **Likely no dbt changes needed.** All four numbers in the strip are produced by metrics that already exist:
  - Total Revenue (Shopify): `fct_orders.total_revenue`.
  - GA4-attributed Revenue: `fct_ga_sessions.ga_total_revenue`.
  - AOV (Shopify): `fct_orders.aov`.
  - Customer Mix: `fct_orders.order_count` and `fct_orders.new_customer_orders` (returning = `order_count` minus `new_customer_orders`).
- **One small addition only if needed.** If, when building the Customer Mix half of the strip, you want a single ready-made "returning orders" metric rather than computing `order_count - new_customer_orders` in the chart, add a `returning_customer_orders` metric on `fct_orders.is_first_order` in `dbt/models/gold/_schema.yml` of the form `type: sum`, `sql: "case when ${TABLE}.is_first_order = 0 then 1 else 0 end"`, `round: 0`. This mirrors the existing `new_customer_orders` metric. If `fct_orders` already carries such a metric (check `_schema.yml` first), reuse it and make no dbt change.
- Tests to add: the underlying keys (`order_id` unique + not_null, `store_id` not_null, `order_month` not_null) are already tested on `fct_orders`, and `fct_ga_sessions` carries `not_null` on `session_date` / `order_month`. If you add the `returning_customer_orders` metric, no new column is introduced (it is a derived metric on an existing column), so no new schema test is required. If this ticket adds any new numeric column, add a `dbt_utils.accepted_range` (`min_value: 0`) range test on it.
- If no metric is added: write "no dbt changes needed" in the PR description.

## Lightdash work
- Tile type: **big number(s)** arranged as a KPI strip. Per generator rule 5 the strip is one tile / one ticket, but Lightdash big-number tiles each show a single metric, so the "strip" is implemented as a **row of up to four big-number tiles** placed side by side under the page-12 heading on the iS Clinical KPI Report dashboard, mirroring the PDF layout. It sits at the top of the dashboard, above the GA4 channel breakdown table built by ticket 006, and after the headline big numbers from tickets 001 to 004.
  - Tile 1, Total Revenue (Shopify): reuse the tile built by ticket 001 (`001: iS Clinical Shopify Revenue`, the `fct_orders.total_revenue` big number) if it is already on the dashboard. Do **not** create a duplicate chart for the same number; if ticket 001's tile is present, this ticket places the remaining three tiles around it.
  - Tile 2, Revenue (GA4-attributed): big number on the `fct_ga_sessions` explore, metric `ga_total_revenue`.
  - Tile 3, AOV (Shopify): big number on the `fct_orders` explore, metric `aov`.
  - Tile 4, Customer Mix (Shopify): big number(s) on the `fct_orders` explore showing the new / returning split. Implement as the new-customer share, label "Customer Mix (new %)", or as two adjacent big numbers; match the PDF "36% / 64%" framing as closely as the big-number tile type allows.
- The `lightdash/charts/<slug>.yml` files to create or adapt (one file per tile). Before creating any new chart YAML, check `lightdash/charts/` for an existing chart that already fits and adapt it instead:
  - `lightdash/charts/combined-shopify-revenue.yml` and `lightdash/charts/combined-meta-spend.yml` are good big-number templates to adapt.
  - `lightdash/charts/average-order-value.yml` already exists and is a strong starting point for the AOV tile, adapt it (scope to iS Clinical, `fct_orders` explore, `aov` metric).
  - `lightdash/charts/sessions.yml` reads the `fct_ga_sessions` explore and is a useful reference for the GA4-attributed revenue tile (same explore, different metric).
  - For Customer Mix, `lightdash/charts/new-customer.yml` and `lightdash/charts/new-vs-repeat-orders-by-month.yml` are useful references for the new-vs-returning split.
  - Create the new big-number chart files needed (suggested slugs: `isclinical-ga4-attributed-revenue.yml`, `isclinical-aov.yml`, `isclinical-customer-mix.yml`) only where no existing chart can be adapted.
- Update `lightdash/dashboards/kpi-report.yml` to add the tiles, laid out as a row to mirror the PDF strip.
- **Mandatory:** every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 12 (IS CLINICAL, 1. REVENUE & CHANNEL ATTRIBUTION)`.
- How the tiles pick up the dashboard's Month filter: the dashboard Month filter is on `fct_orders_order_month_label`. The `fct_orders`-backed tiles (Total Revenue, AOV, Customer Mix) pick it up directly. The `fct_ga_sessions`-backed tile (GA4-attributed Revenue) exposes a matching `order_month_label` additional dimension (`to_char(order_month, 'YYYY-MM')`), so Lightdash cross-applies the filter by field name: cross-apply the Month filter onto `fct_ga_sessions_order_month_label` via `tileTargets` in `kpi-report.yml`. Confirm `order_month_label` is present on both the `fct_orders` and `fct_ga_sessions` explores before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read each tile value in the strip.
- Assert they equal the April 2026 iS Clinical values stated in the "PDF reference" section above: Total Revenue **£144,532**, GA4-attributed Revenue **£73,808**, AOV **£134.45**, Customer Mix **36% / 64%** (385 new / 690 returning).
- If a value does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or a known data-availability gap from section (c), and note the cause in the ticket. The three Shopify-derived numbers (Total Revenue, AOV, Customer Mix) are expected to read slightly low against the PDF because of the documented ~2.6% iS Clinical Shopify sync gap (April 2026 Bronze holds 1,047 orders vs 1,075). If the only discrepancy is that gap, merge is still acceptable (the tiles are correctly wired); the Basecamp closing comment must state the live values, name the gap, and link the "fix iS Clinical Shopify sync" prerequisite ticket. The GA4-attributed Revenue tile should match £73,808 exactly.

## Snowflake fallback SQL
The ground-truth check. Reproduce the numbers directly from Snowflake (via `snow sql -c hgi`):
```sql
-- Shopify: total revenue, order count, AOV, new-vs-returning split
select
    sum(total_price)                                  as total_revenue_shopify,
    count(distinct order_id)                          as order_count,
    round(sum(total_price) / count(distinct order_id), 2) as aov,
    sum(is_first_order)                               as new_orders,
    count(distinct order_id) - sum(is_first_order)    as returning_orders
from HGI.GOLD.FCT_ORDERS
where store_id = 'isclinical'
  and order_month = '2026-04-01';

-- GA4-attributed revenue
select sum(total_revenue) as ga4_attributed_revenue
from HGI.GOLD.FCT_GA_SESSIONS
where store_id = 'isclinical'
  and order_month = '2026-04-01';
```
Expected per the PDF: `total_revenue_shopify` near `144532`, `aov` near `134.45`, `new_orders` near `385`, `returning_orders` near `690`, `ga4_attributed_revenue` = `73808`. The Shopify figures will read slightly low (around 2.6%) because of the documented iS Clinical Shopify sync gap (Bronze held 1,047 orders for April 2026, not 1,075). If the Shopify shortfall matches that ~2.6%, the gap is the known Airbyte data-availability gap, not a model defect.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket on its own does not introduce any of those, it is a presentation-layer change over existing models; no CLAUDE.md update is expected.
