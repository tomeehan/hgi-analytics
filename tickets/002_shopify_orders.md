# 002: iS Clinical Shopify Orders

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-002-shopify_orders`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-002-shopify_orders`.
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
- April 2026 value (iS Clinical): **1,075 orders**.
- The figure also appears on page 12 under the headline Total Revenue tile ("1,075 orders, source of truth") and as the AOV denominator ("£144,532 / 1,075 orders"), and again on page 14 in section "4. Customer Mix & 5. AOV Split" as the Overall row ("1,075 orders, 100%"). All three are the same number: the count of iS Clinical Shopify orders placed in April 2026.

## Metric definition
- Plain English description of what the metric counts: the number of distinct Shopify orders placed on the iS Clinical store within the selected calendar month. The PDF labels this "1,075 orders" and treats Shopify as the source of truth for it.
- Source of truth chain per the PDF appendix (Shopify, GA4, Meta, Google Ads, Klaviyo): Shopify is the source of truth for order count. GA4 reports transactions separately (a channel-attributed view); they are not the same number and this tile does not use GA4.
- Filter behaviour: how the tile responds to the dashboard's **Month** filter: the tile reads `fct_orders.order_count`, a `count_distinct` on `order_id`. The `fct_orders` explore exposes `order_month_label` (a `YYYY-MM` string), the exact field the dashboard's Month filter targets, so the tile scopes to the selected month automatically. With the Month filter on April 2026 (`2026-04`) the tile shows the April order count.

## Data dependencies
- Bronze sources needed (with current status from generator section (c): ok loaded, blocked on Airbyte, or partial): `BRONZE_SHOPIFY_ISCLINICAL`. **Degraded.** The iS Clinical Shopify Airbyte sync authenticates with a rotating OAuth token (not a static custom-app token). The token fails mid-sync, and when it does Airbyte silently drops scattered records rather than erroring loudly. Bronze runs roughly **2.6% short** for a full month. For April 2026, Bronze holds **1,047 orders** against the **1,075** stated in the PDF. The PDF figure is authoritative; the live tile will read slightly low (around 1,047) until the sync is fixed. This must be noted at verification. Prerequisite: a separate data-engineering ticket to "fix iS Clinical Shopify sync" (rotate to a stable token / harden the connector). If that ticket does not exist yet, raise it; this tile cannot read the full 1,075 until it lands.
- Silver and Gold models that already cover this (file paths under `dbt/models/`): `dbt/models/gold/fct_orders.sql` already produces the order grain and declares the `order_count` metric (`count_distinct` on `order_id`) in `dbt/models/gold/_schema.yml`. It carries `order_month` (a DATE) plus the `order_month_label` additional dimension (`YYYY-MM` string) used by the dashboard Month filter. `fct_orders` is fed by `dbt/models/silver/stg_shopify__orders.sql`.
- New Silver or Gold models or columns required, if any: none. The metric, the grain and the month dimension all already exist.

## dbt work
- Exact models to add or modify, with rationale: no dbt changes needed. `fct_orders.order_count` and `fct_orders.order_month_label` already exist and are sufficient.
- Tests to add (`not_null` and `unique` on keys, range tests on numeric outputs): none. `order_id` already carries `not_null` and `unique` tests in `dbt/models/gold/_schema.yml`.
- If none required, write "no dbt changes needed": no dbt changes needed.

## Lightdash work
- Tile type (big number, bar chart, table, pie, markdown) and where on the iS Clinical KPI Report dashboard it sits (which row, under which heading, mirroring the PDF page order): big number tile. It sits in the top KPI row of the iS Clinical KPI Report dashboard, immediately after the iS Clinical Shopify Revenue tile from ticket 001, mirroring the PDF page 12 "Revenue & Channel Attribution" headline strip where order count sits alongside revenue.
- The `lightdash/charts/<slug>.yml` file to create or adapt (one per tile), plus the update to `lightdash/dashboards/kpi-report.yml` to place the tile: an existing chart `lightdash/charts/combined-shopify-orders.yml` already fits this tile (big number on `fct_orders` using `fct_orders_order_count`, `limit: 1`) and is already placed on `kpi-report.yml`. Adapt it rather than writing a new chart: rename it to the single-brand framing (for example `name: iS Clinical Shopify Orders`, `slug: isclinical-shopify-orders`, and update its `label` and `description`) so the dashboard reads as iS Clinical only, and update the corresponding tile entry in `lightdash/dashboards/kpi-report.yml` to point at the renamed chart. Do not add a brand filter to the chart: ticket 001 rescopes the whole dashboard and the warehouse only holds iS Clinical Shopify data, so `fct_orders_order_count` is iS Clinical by construction.
- Mandatory: every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page <N> (<section title>)`. For this tile that is exactly: `# Source: April 2026 KPI Report, page 12 (Revenue & Channel Attribution)`. Add it as the first line of the chart YAML you adapt and of `lightdash/dashboards/kpi-report.yml` if you edit it.
- Before creating a new chart YAML, check `lightdash/charts/` for an existing chart that already fits and adapt it instead: `lightdash/charts/combined-shopify-orders.yml` is the existing chart; adapt it (see above).
- How the tile picks up the dashboard's Month filter: the underlying explore **must** expose `order_month` (or an equivalent month-truncated date dimension), matching the field used by `lightdash/dashboards/kpi-report.yml`. Confirm this before editing the YAML: confirmed. The tile's explore is `fct_orders`, and the dashboard Month filter targets `fct_orders_order_month_label`, which `fct_orders` exposes as an additional dimension on `order_month`. No `tileTargets` cross-apply is needed because the tile uses the same explore as the filter's home field.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile value.
- Assert it equals the April 2026 iS Clinical value stated in the "PDF reference" section above (`1,075`).
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or a known data-availability gap from section (c), and note the cause in the ticket. Expected outcome: the live tile reads around **1,047**, not 1,075, because of the degraded iS Clinical Shopify Airbyte sync (see "Data dependencies"). A live value near 1,047 that matches the Snowflake fallback SQL is the known sync gap, not a model bug: note it on the card and link the "fix iS Clinical Shopify sync" prerequisite ticket. A value that differs from both 1,075 and the Snowflake count is a real bug and blocks merge.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
select count(distinct order_id) as order_count
from hgi.gold.fct_orders
where store_id = 'isclinical'
  and order_month = date '2026-04-01';
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section).
