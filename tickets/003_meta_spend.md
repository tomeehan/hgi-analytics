# 003: iS Clinical Meta Spend

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-003-meta_spend`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-003-meta_spend`.
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
- Page 15, section "IS CLINICAL, 6. Paid Media Performance" (the "Meta Ads, remarketing vs acquisition" panel).
- April 2026 value (iS Clinical): **£7,657** (the panel's "Total Meta" row reads £7,657.47; £2,636.06 remarketing + £3,215.96 acquisition + £1,805.45 Skin Quiz lead campaign).

## Metric definition
- Total iS Clinical Meta (Facebook Marketing) ad spend for the month: the sum of daily spend across every iS Clinical Meta ad set, in GBP.
- Source of truth chain per the PDF appendix: **Meta**. The PDF Paid Media Performance page is labelled "META (7D CLICK + 1D VIEW)". Spend itself is attribution-window independent (the window only affects attributed purchases/ROAS); this tile reports raw spend.
- Filter behaviour: a single big-number tile that responds to the dashboard's **Month** filter. With the Month filter on April 2026 it reads total iS Clinical Meta spend for April 2026; changing the month rescopes it.

## Data dependencies
- Bronze source needed: `BRONZE_META_ISCLINICAL` (`ADS_INSIGHTS` family). Status per generator section (c): **Live** for iS Clinical (one Meta ad account per brand, syncing on a 24h schedule). No sync-gap caveat applies; the Shopify rotating-OAuth degradation is Shopify-only and does not touch Meta.
- Silver and Gold models that already cover this:
  - `dbt/models/silver/stg_meta__ads_spend.sql` (Silver staging, daily Meta spend per `store_id`).
  - `dbt/models/gold/fct_ad_spend.sql` (Gold fact, one row per `spend_date` x `store_id`; `select * from {{ ref('stg_meta__ads_spend') }}`).
- New Silver or Gold models or columns required: none. `fct_ad_spend` already exposes a `spend` column, a `total_meta_spend` metric, a `store_id` brand dimension, and an `order_month` / `order_month_label` pair.

## dbt work
- No dbt changes needed. `fct_ad_spend` and its `total_meta_spend` metric (`type: sum`, `format: gbp`, declared on the `spend` column in `dbt/models/gold/_schema.yml`) already produce this number. `order_month_label` is already declared as an additional dimension on `fct_ad_spend.order_month`, mirroring `fct_orders.order_month_label`, so the dashboard Month filter cross-applies.
- Tests to add: none. Keys are already covered (`not_null` on `spend_date` and `store_id` in `_schema.yml`). If a range test is wanted on `spend`, add a `dbt_utils.accepted_range` with `min_value: 0`, but this is optional and out of scope for this tile.

## Lightdash work
- Tile type: **big number**. It sits in the headline KPI strip area of the iS Clinical KPI Report dashboard, alongside the other big-number tiles produced by this batch (`001` Shopify Revenue, `002` Shopify Orders, `004` Klaviyo Revenue), mirroring the report's top-line metrics. Place it as the next big-number tile in dashboard reading order after ticket `002`.
- Create or adapt `lightdash/charts/meta-spend.yml` (one file per tile). The tile is a big-number chart on the `fct_ad_spend` explore, selecting the `total_meta_spend` metric. Before creating a new chart YAML, check `lightdash/charts/` for an existing Meta-spend chart (a prior cross-brand "Meta Spend Share by Brand" tile may exist from before the dashboard was rescoped) and adapt it to a single-value iS Clinical big number instead of writing a new file. Then update `lightdash/dashboards/kpi-report.yml` to add the tile.
- Mandatory: every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 15 (Paid Media Performance)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is defined on `fct_orders_order_month_label`. The `fct_ad_spend` explore exposes `order_month_label` (an additional dimension on `order_month`, identical SQL `to_char(order_month, 'YYYY-MM')`), so Lightdash cross-applies the filter by matching field name via `tileTargets`. Confirm `order_month_label` is present on the `fct_ad_spend` explore before editing the YAML, and that the tile's `tileTargets` maps the dashboard Month filter onto `fct_ad_spend_order_month_label`.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile value.
- Assert it equals the April 2026 iS Clinical value stated in the "PDF reference" section above: **£7,657** (the PDF gives £7,657.47; the metric is rounded to whole pounds via `round: 0`).
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
select
    to_char(order_month, 'YYYY-MM') as order_month_label,
    round(sum(spend), 2) as total_meta_spend
from HGI.GOLD.FCT_AD_SPEND
where store_id = 'isclinical'
  and order_month = '2026-04-01'
group by 1;
-- expect total_meta_spend ~= 7657.47, matching the PDF page 15 "Total Meta" row.
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This tile uses the existing Meta source and `fct_ad_spend` model, so no `CLAUDE.md` change is expected.
