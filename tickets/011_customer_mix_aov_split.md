# 011: Customer mix & AOV split

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-011-customer_mix_aov_split`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement dbt changes (if any).** Edit the models listed in the "dbt work" section, then run `cd dbt && dbt build --select <model>+` and confirm tests pass. If there are no dbt changes, skip this step.
4. **Edit the Lightdash YAML.**
   - Run `lightdash download` from the repo root to refresh the local `lightdash/charts/` and `lightdash/dashboards/` YAML from production, so you start editing from live state.
   - Before creating a new chart YAML, check `lightdash/charts/` for an existing chart that already fits this tile and adapt it instead of writing a new one.
   - Edit or create `lightdash/charts/customer-mix-aov-split.yml` (one file per tile) and update `lightdash/dashboards/kpi-report.yml` to add the tile.
   - Every chart and dashboard YAML file you create or edit **must** carry, as the very first line, a comment in the exact form `# Source: April 2026 KPI Report, page <N> (<section title>)`.
   - `lightdash lint` to validate the YAML against Lightdash's JSON schema. Optionally `lightdash run-chart lightdash/charts/customer-mix-aov-split.yml` to confirm the query runs against the warehouse.
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
   - `git push -u origin ticket-011-customer_mix_aov_split`.
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
- Page 14, section "4. Customer Mix & 5. AOV Split" (the iS Clinical traffic / customer-mix page; the panel is qualified "Shopify (source of truth)").
- April 2026 value (iS Clinical): the customer mix and AOV split table reads as follows.

| Segment | Orders | % orders | Revenue | % revenue | AOV |
|---|---|---|---|---|---|
| New customers | 385 | 35.8% | £45,038 | 31.2% | £116.98 |
| Returning customers | 690 | 64.2% | £99,494 | 68.8% | £144.19 |
| **Overall** | **1,075** | **100%** | **£144,532** | **100%** | **£134.45** |

## Metric definition
- This tile splits the month's iS Clinical Shopify orders into **new customers** (their first ever order) and **returning customers** (any later order), and reports five columns per segment plus an overall row: order count, share of orders, revenue, share of revenue, and average order value (AOV = revenue / orders).
- A "new customer" order is one where the order is that customer's first ever order across all time, not just within the month. `fct_orders.is_first_order` is a 0/1 integer flag computed as `row_number() over (partition by customer_id order by created_at) = 1`, so `SUM(is_first_order)` gives the new-customer order count and `COUNT(*) - SUM(is_first_order)` gives returning.
- Source of truth chain per the PDF appendix: **Shopify**. The PDF panel header explicitly labels this "Shopify (source of truth)". No GA4, Meta, Google Ads or Klaviyo input.
- Filter behaviour: the table responds to the dashboard's **Month** filter. With the Month filter on April 2026, every row is scoped to orders created in that calendar month. Changing the filter rescopes the new / returning / overall split to the selected month.

## Data dependencies
- **Bronze sources needed:** `BRONZE_SHOPIFY_ISCLINICAL` (Shopify orders). **Status: degraded.** The iS Clinical Shopify Airbyte sync authenticates with a rotating OAuth token that fails mid-sync; when it does, Airbyte silently drops scattered records instead of erroring loudly. Bronze ends up roughly **2.6% short** per month. For April 2026, Bronze holds **1,047 orders** against the **1,075** stated in the PDF. The new / returning split, both order counts and revenue, will therefore read slightly low until the sync is fixed. The PDF figure (1,075 overall) is authoritative. This is tracked by the prerequisite data-engineering ticket **"fix iS Clinical Shopify sync"** (rotating OAuth token). If that ticket does not exist yet, create it: the fix is to move the iS Clinical Shopify source onto a stable custom-app token and backfill April 2026.
- **Silver and Gold models that already cover this:**
  - `dbt/models/silver/stg_shopify__orders.sql` (Silver staging, iS Clinical orders).
  - `dbt/models/gold/fct_orders.sql` (Gold fact; carries `is_first_order` as a 0/1 integer and `order_month` as a month-truncated date).
  - `dbt/models/gold/dim_customers.sql` exists but is not required for this tile: the new vs returning split is driven entirely by `fct_orders.is_first_order`.
- **New Silver or Gold models or columns required:** none. `fct_orders` already exposes `is_first_order`, `net_sales` / `total_price`, and `order_month`. The new / returning / overall table is a Lightdash explore on `fct_orders` only.

## dbt work
- No dbt changes needed. `fct_orders` already carries `is_first_order` (0/1 integer), `order_month`, and the revenue columns. Verify the existing `not_null` and `unique` tests on `fct_orders.order_id` and the `not_null` test on `is_first_order` are present in `dbt/models/gold/_schema.yml`; if a range/`accepted_values` test on `is_first_order` (expecting `0` or `1`) is missing, add it in the same PR.

## Lightdash work
- **Tile type:** table. It sits on the iS Clinical KPI Report dashboard in the customer-mix row, mirroring PDF page 14: directly after the PR & media highlights tile (ticket 010) and before the Meta remarketing vs acquisition tile (ticket 012), under the iS Clinical traffic / customer-mix heading.
- **Chart YAML:** create or adapt `lightdash/charts/customer-mix-aov-split.yml` (one file per tile). The table has three rows (new, returning, overall) and five value columns (orders, % orders, revenue, % revenue, AOV). Build it as a table chart on the `fct_orders` explore grouped by a new vs returning dimension derived from `is_first_order` (a `case when is_first_order = 1 then 'New customers' else 'Returning customers' end` dimension), with metrics for order count, revenue, AOV, and percentage-of-total metrics for % orders and % revenue. The overall row is the table total. Before creating a new chart YAML, check `lightdash/charts/` for an existing table chart (for example the channel breakdown table from ticket 006) that already fits and adapt it instead.
- **Dashboard YAML:** update `lightdash/dashboards/kpi-report.yml` to add the tile in the customer-mix row.
- **Mandatory Source comment:** every chart and dashboard YAML file created or edited must have, as its very first line, a comment in the exact form `# Source: April 2026 KPI Report, page 14 (4. Customer Mix & 5. AOV Split)`.
- **Month filter wiring:** the underlying explore is `fct_orders`, which exposes `order_month` (and `order_month_label`, the field the dashboard Month filter uses). This matches the field used by `lightdash/dashboards/kpi-report.yml`, so the dashboard Month filter applies directly with no `tileTargets` remap needed. Confirm `order_month_label` is exposed on the `fct_orders` explore before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert the segments equal the April 2026 iS Clinical values stated in the "PDF reference" section above: new customers `385` orders / £45,038, returning customers `690` orders / £99,494, overall `1,075` orders / £144,532, with AOV `£116.98` / `£144.19` / `£134.45`.
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or the known iS Clinical Shopify sync gap from section (c). The expected live shortfall is roughly 2.6% (overall around 1,047 orders rather than 1,075); a gap of that size is the known sync gap and should be noted in the Basecamp comment, not treated as a bug. A larger or differently shaped gap is a model issue and must be fixed before merge.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
select
    case when is_first_order = 1 then 'New customers' else 'Returning customers' end as segment,
    count(*)                                          as orders,
    round(sum(net_sales), 0)                          as revenue,
    round(sum(net_sales) / nullif(count(*), 0), 2)    as aov
from hgi.gold.fct_orders
where store_id = 'isclinical'
  and order_month = '2026-04-01'
group by 1

union all

select
    'Overall'                                         as segment,
    count(*)                                          as orders,
    round(sum(net_sales), 0)                          as revenue,
    round(sum(net_sales) / nullif(count(*), 0), 2)    as aov
from hgi.gold.fct_orders
where store_id = 'isclinical'
  and order_month = '2026-04-01'
order by segment;
```
Note: the `net_sales` column on `fct_orders` is `total_price` minus refunds. If the preview tile is built on `total_price` (gross) rather than `net_sales`, swap the column here to match so the comparison is apples to apples. Either way the expected overall is 1,075 orders / £144,532 per the PDF, with the ~2.6% sync shortfall applied to the live figure.

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket is not expected to need a `CLAUDE.md` change: it reuses the existing `fct_orders` model and the `is_first_order` convention already documented there.
