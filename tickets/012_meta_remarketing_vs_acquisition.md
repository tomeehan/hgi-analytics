# 012: Meta ads remarketing vs acquisition

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-012-meta_remarketing_vs_acquisition`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-012-meta_remarketing_vs_acquisition`.
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
- Page 15, section "IS CLINICAL, 6. Paid Media Performance" (the "META ADS, REMARKETING VS ACQUISITION" panel, left-hand table; the page is labelled "META (7D CLICK + 1D VIEW)").
- April 2026 value (iS Clinical): the panel is a five-column table (audience type, spend, purchases, revenue, ROAS, CPA) with three audience-type rows plus a total:

  | Audience type | Spend | Purchases | Revenue | ROAS | CPA |
  |---|---|---|---|---|---|
  | Remarketing | £2,636.06 | 261 | £38,699 | 14.68x | £10.10 |
  | Acquisition (cold) | £3,215.96 | 141 | £17,889 | 5.56x | £22.81 |
  | Skin Quiz lead campaign | £1,805.45 | 4 | £525 | 0.29x | £451.36 |
  | **Total Meta** | **£7,657.47** | **406** | **£57,113** | **7.46x** | **£18.86** |

  The headline verification numbers are: total Meta spend **£7,657.47**, **406** purchases, revenue **£57,113**, ROAS **7.46x**. The "Skin Quiz lead campaign" row is the report's "other" audience type (a lead-generation campaign, not a sales campaign); the PDF footnote on the panel reads "Skin Quiz campaign optimises for leads, not purchases, the £525 attributed revenue is a lower-bound number."

## Metric definition
- A table of iS Clinical Meta (Facebook Marketing) paid-ads performance for the month, split by **audience type** into three rows (remarketing, acquisition, other) plus a total. For each audience type the table shows: **spend** (sum of daily Meta spend in GBP), **purchases** (count of attributed purchase actions), **revenue** (sum of attributed purchase value in GBP), **ROAS** (revenue divided by spend) and **CPA** (spend divided by purchases).
- Audience type is derived from the Meta campaign / ad-set naming convention, not a native Meta field:
  - **Remarketing**: campaign or ad-set name contains `REMARKETING`, `RETARGETING` or `EXISTING CUSTOMERS`.
  - **Acquisition**: campaign or ad-set name contains `PROSPECTING`, `ACQUISITION` or `LOOKALIKE`.
  - **Other**: everything else, dominated by the Skin Quiz lead campaign (campaign name contains `SKIN QUIZ`, `objective = 'OUTCOME_LEADS'`). The PDF labels this row "Skin Quiz lead campaign".
- Source of truth chain per the PDF appendix: **Meta**. The page is labelled "META (7D CLICK + 1D VIEW)", a 7-day click plus 1-day view attribution window. Spend is attribution-window independent; purchases and revenue come from the `ACTIONS` / `ACTION_VALUES` JSON arrays where `action_type = 'purchase'`, which is the value Meta reports under that account's default attribution setting.
- Filter behaviour: a table tile that responds to the dashboard's **Month** filter. With the Month filter on April 2026 the table shows the three audience-type rows for April 2026; changing the month rescopes every row.

## Data dependencies
- Bronze source needed: `BRONZE_META_ISCLINICAL` (`ADS_INSIGHTS` family). Status per generator section (c): **Live** for iS Clinical (one Meta ad account per brand, syncing on a 24h schedule). No sync-gap caveat applies; the Shopify rotating-OAuth degradation is Shopify-only and does not touch Meta.
- Silver and Gold models that currently cover Meta:
  - `dbt/models/silver/stg_meta__ads_spend.sql` (Silver staging). It aggregates each brand's raw `ADS_INSIGHTS` table to **one row per `spend_date`** (`group by date_start`), summing spend, impressions, clicks, purchases and purchase value. Campaign and ad-set metadata (`campaign_name`, `adset_name`, `objective`) is dropped in this aggregation.
  - `dbt/models/gold/fct_ad_spend.sql` (Gold fact, one row per `spend_date` x `store_id`; `select * from {{ ref('stg_meta__ads_spend') }}`). It exposes `spend`, `purchases`, `purchase_value`, a `total_meta_spend` metric, a `store_id` brand dimension, and an `order_month` / `order_month_label` pair.
- **New columns required:** `fct_ad_spend` does **not** carry an audience-type dimension. The current grain (`spend_date` x `store_id`) collapses every campaign together, so the report's remarketing-vs-acquisition split cannot be produced from the model as it stands. This tile needs new dbt work, see the "dbt work" section below: the staging model must keep an `audience_type` classification, and the Gold fact must regrain on it.

## dbt work
This tile needs dbt changes. The audience-type split does not exist in `fct_ad_spend` today.

- **Modify `dbt/models/silver/stg_meta__ads_spend.sql`.** Add an `audience_type` column derived from the campaign / ad-set naming convention, and change the per-brand aggregation grain from `date_start` to `(date_start, audience_type)`. Concretely, in each brand's `_raw` CTE add a classifying expression, for example:
  ```sql
  case
    when upper(campaign_name || ' ' || adset_name) like '%REMARKETING%'
      or upper(campaign_name || ' ' || adset_name) like '%RETARGETING%'
      or upper(campaign_name || ' ' || adset_name) like '%EXISTING CUSTOMERS%'
      then 'remarketing'
    when upper(campaign_name || ' ' || adset_name) like '%PROSPECTING%'
      or upper(campaign_name || ' ' || adset_name) like '%ACQUISITION%'
      or upper(campaign_name || ' ' || adset_name) like '%LOOKALIKE%'
      then 'acquisition'
    else 'other'
  end as audience_type
  ```
  Then `group by date_start, audience_type` in the `_base_daily`, `_purchases_daily` and `_purchase_value_daily` CTEs, and carry `audience_type` through the final `select`. (April 2026 sample confirms the convention holds: prospecting / lookalike ad sets vs remarketing / existing-customer ad sets vs the Skin Quiz `OUTCOME_LEADS` campaign. Validate the classification against the PDF totals before merging, see the Snowflake fallback SQL.)
- **Modify `dbt/models/gold/fct_ad_spend.sql`.** It is currently `select * from {{ ref('stg_meta__ads_spend') }}`; the new `audience_type` column flows through automatically. The fact's grain becomes `spend_date` x `store_id` x `audience_type`.
- **Update `dbt/models/gold/_schema.yml`** for `fct_ad_spend`:
  - Update the model description to note the new `audience_type` grain.
  - Add an `audience_type` dimension. Give it a human-readable label and, optionally, a `case` that maps `remarketing -> Remarketing`, `acquisition -> Acquisition`, `other -> Other` for display.
  - Add the metrics the table needs if they are not already declared: `total_meta_purchases` (`type: sum` on `purchases`), `total_meta_revenue` (`type: sum`, `format: gbp` on `purchase_value`). `total_meta_spend` already exists. ROAS and CPA are ratios: prefer a Lightdash table calculation (`revenue / spend`, `spend / purchases`) over a dbt metric, since they do not aggregate additively.
- **Tests:** the existing `not_null` on `spend_date` and `store_id` stay. Add `not_null` on `audience_type`, and `accepted_values` with `values: ['remarketing', 'acquisition', 'other']`. Optionally a `dbt_utils.accepted_range` with `min_value: 0` on `spend`, `purchases` and `purchase_value`.
- Run `cd dbt && dbt build --select stg_meta__ads_spend+ fct_ad_spend+` and confirm all tests pass.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard under the "Paid Media Performance" heading (PDF page 15), as the left-hand panel of that section, mirroring the PDF's "META ADS, REMARKETING VS ACQUISITION" table. Place it in dashboard reading order after ticket `011` (Customer mix & AOV split) and before ticket `013` (Paid search / shopping), which is the right-hand panel of the same PDF page.
- Create `lightdash/charts/meta-remarketing-vs-acquisition.yml` (one file per tile). The tile is a table chart on the `fct_ad_spend` explore, with:
  - the `audience_type` dimension as the row grouping (three rows: remarketing, acquisition, other),
  - the `total_meta_spend`, `total_meta_purchases` and `total_meta_revenue` metrics as columns,
  - two table calculations for **ROAS** (`total_meta_revenue / total_meta_spend`, formatted as a multiplier, for example `7.46x`) and **CPA** (`total_meta_spend / total_meta_purchases`, formatted `gbp`).
  - Before creating a new chart YAML, check `lightdash/charts/` for an existing Meta-spend or ad-spend chart (a prior cross-brand "Meta Spend Share by Brand" tile may exist) and adapt it to this single-brand audience-type table instead of writing a new file from scratch.
  - Then update `lightdash/dashboards/kpi-report.yml` to add the tile.
- Mandatory: every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 15 (Paid Media Performance)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is defined on `fct_orders_order_month_label`. The `fct_ad_spend` explore exposes `order_month_label` (an additional dimension on `order_month`, identical SQL `to_char(order_month, 'YYYY-MM')`), so Lightdash cross-applies the filter by matching field name via `tileTargets`. Confirm `order_month_label` is present on the `fct_ad_spend` explore before editing the YAML, and that the tile's `tileTargets` maps the dashboard Month filter onto `fct_ad_spend_order_month_label`.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert it reproduces the April 2026 iS Clinical values from the "PDF reference" section above: the three audience-type rows sum to total Meta spend **£7,657.47**, **406** purchases, revenue **£57,113**, ROAS **7.46x**; the remarketing row reads ~£2,636 spend / ~£38,699 revenue / 14.68x ROAS, and the acquisition row reads ~£3,216 spend / ~£17,889 revenue / 5.56x ROAS.
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (likely the `audience_type` classification not matching the PDF's bucketing) or a known data-availability gap from section (c), and note the cause in the ticket. The most likely failure mode is a campaign whose name does not match the classification rules, landing in the wrong bucket; tune the `case` expression until the per-row totals match the PDF.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`). This runs the classification straight against Bronze so you can validate the audience-type buckets before wiring dbt:
```sql
with classified as (
    select
        date_start as spend_date,
        case
            when upper(campaign_name || ' ' || adset_name) like '%REMARKETING%'
              or upper(campaign_name || ' ' || adset_name) like '%RETARGETING%'
              or upper(campaign_name || ' ' || adset_name) like '%EXISTING CUSTOMERS%'
                then 'remarketing'
            when upper(campaign_name || ' ' || adset_name) like '%PROSPECTING%'
              or upper(campaign_name || ' ' || adset_name) like '%ACQUISITION%'
              or upper(campaign_name || ' ' || adset_name) like '%LOOKALIKE%'
                then 'acquisition'
            else 'other'
        end as audience_type,
        spend,
        actions,
        action_values
    from HGI.BRONZE_META_ISCLINICAL.ADS_INSIGHTS
    where date_start >= '2026-04-01' and date_start < '2026-05-01'
)
select
    audience_type,
    round(sum(spend), 2) as spend,
    round(sum(p.purchases), 0) as purchases,
    round(sum(rv.revenue), 0) as revenue,
    round(sum(rv.revenue) / nullif(sum(spend), 0), 2) as roas,
    round(sum(spend) / nullif(sum(p.purchases), 0), 2) as cpa
from classified c,
     lateral (
        select sum(case when a.value:action_type::string = 'purchase'
                        then a.value:value::float else 0 end) as purchases
        from lateral flatten(input => c.actions, outer => true) a
     ) p,
     lateral (
        select sum(case when av.value:action_type::string = 'purchase'
                        then av.value:value::float else 0 end) as revenue
        from lateral flatten(input => c.action_values, outer => true) av
     ) rv
group by audience_type
order by audience_type;
-- expect three rows summing to spend ~= 7657.47, purchases ~= 406, revenue ~= 57113;
-- remarketing ~= 2636.06 spend / 38699 rev / 14.68x, acquisition ~= 3215.96 spend / 17889 rev / 5.56x,
-- other (Skin Quiz lead campaign) ~= 1805.45 spend / 525 rev / 0.29x, matching the PDF page 15 panel.
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket establishes a new convention: a Meta `audience_type` classification derived from the campaign / ad-set naming convention (`REMARKETING` / `RETARGETING` / `EXISTING CUSTOMERS` -> remarketing; `PROSPECTING` / `ACQUISITION` / `LOOKALIKE` -> acquisition; else other). It also regrains `fct_ad_spend` from `spend_date` x `store_id` to `spend_date` x `store_id` x `audience_type`. Add a short note to `CLAUDE.md` under the conventions section so a future store onboarding keeps the classification consistent.
