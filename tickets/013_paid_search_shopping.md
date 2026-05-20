# 013: Paid search / shopping

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-013-paid_search_shopping`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-013-paid_search_shopping`.
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
- Page 15, section "IS CLINICAL, 6. Paid Media Performance" (the "GOOGLE ADS, BRANDED VS NON-BRANDED" panel, the right-hand table; the panel sub-label reads "search term raw report" and the page header reads "GOOGLE ADS (1D CLICK + 1D VIEW)").
- April 2026 value (iS Clinical): the panel is a four-column table (type, clicks, cost, conversions, % of cost) with two type rows plus a total:

  | Type | Clicks | Cost | Conv | % of cost |
  |---|---|---|---|---|
  | Branded ("is clinical", product names, misspellings) | 1,209 | £4,678 | 159 | 92.2% |
  | Non-branded (acquisition) | 17 | £397 | 3 | 7.8% |
  | **Total (top 100 by cost)** | **1,226** | **£5,076** | **162** | **100%** |

  The headline verification numbers are: total clicks **1,226**, total cost **£5,076**, total conversions **162**. The branded row is **92.2% of cost** and the non-branded row **7.8%**. The PDF footnote on the panel reads "Top 100 search terms by cost (covers ~65% of Google Ads spend, £7,815 total). Account ROAS 3.58x. Top non-branded terms: 'high end skincare brands', 'home facial kit', 'skincare products for rosacea'." So the table deliberately covers only the **top 100 search terms by cost** (~65% of the £7,815 total account spend), not the full account.

## Metric definition
- A table of iS Clinical Google Ads search-term performance for the month, split by **brand intent** into two rows (branded, non-branded) plus a total. For each type the table shows: **clicks** (sum of clicks), **cost** (sum of cost in GBP), **conversions** (sum of conversions) and **% of cost** (that row's cost as a share of the table's total cost).
- The table is scoped to the **top 100 search terms by cost** for the month, which the PDF footnote says covers ~65% of total Google Ads spend (£7,815 for the account). It is a search-term raw report, not the full campaign-level account.
- Brand intent is derived from the search-term text, not a native Google Ads field:
  - **Branded**: the search term contains the brand name or a product name (`is clinical`, `isclinical`, `is-clinical`, common misspellings, iS Clinical product names).
  - **Non-branded (acquisition)**: everything else, generic skincare-intent terms such as "high end skincare brands", "home facial kit", "skincare products for rosacea".
- Source of truth chain per the PDF appendix: **Google Ads**. The page is labelled "GOOGLE ADS (1D CLICK + 1D VIEW)", a 1-day click plus 1-day view attribution window. Clicks and cost come from the Google Ads search-query / search-term stream; conversions come from the same stream's `conversions` metric.
- Filter behaviour: a table tile that responds to the dashboard's **Month** filter. With the Month filter on April 2026 the table shows the two brand-intent rows for April 2026; changing the month rescopes every row.

## Data dependencies
- Bronze source needed: `BRONZE_GOOGLE_ADS_ISCLINICAL`. Status per generator section (c): **Live** for iS Clinical, the full Airbyte stream set is loaded (campaign, ad group, keyword, search query, shopping product, geo, age/gender, etc). No sync-gap caveat applies; the Shopify rotating-OAuth degradation is Shopify-only and does not touch Google Ads.
- **Google Ads is in Bronze but completely unmodelled.** Verified against the repo on 2026-05-20:
  - `dbt/models/bronze/_sources.yml` declares no Google Ads source. It declares `bronze_google_analytics_isclinical` (GA4, schema `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL`), which is a different source. There is **no** `bronze_google_ads_isclinical` entry.
  - There is **no** Silver `stg_google_ads__*` model and **no** Gold `fct_*` / `dim_*` model over Google Ads. The only Google-prefixed dbt models are the GA4 staging models `dbt/models/silver/stg_google_analytics__sessions.sql` and `dbt/models/silver/stg_google_analytics__transactions.sql`, plus the GA4-derived `dbt/models/gold/fct_ga_sessions.sql`. None of these touch Google Ads.
  - `dbt/models/gold/fct_ad_spend.sql` is **Meta-only** (it `select * from {{ ref('stg_meta__ads_spend') }}`). The `_schema.yml` description for `fct_ad_spend` even states "Google Ads pending source-side fix"; that note predates the Bronze landing and is now stale.
- Silver and Gold models that already cover this tile: **none**. This tile cannot be built from any existing model. It needs the full dbt stack (Bronze source declaration, Silver staging, Gold fact) created from scratch, see the "dbt work" section below.

## dbt work
This tile needs new dbt work. There is no Google Ads model in the project today; it must be built end to end.

- **Declare the Bronze source.** Add a `bronze_google_ads_isclinical` source to `dbt/models/bronze/_sources.yml`, schema `BRONZE_GOOGLE_ADS_ISCLINICAL`, with the search-query / search-term table listed (inspect the schema in Snowflake first, the Airbyte Google Ads connector typically lands `search_query_performance_report` or similar, plus campaign / ad-group streams). List only the streams this tile needs.
- **Create the Silver staging model `dbt/models/silver/stg_google_ads__search_terms.sql`.** One row per `(search_date, search_term)` (or per `(search_date, search_term, campaign)` if the raw stream is finer). Type the columns, select `clicks`, `cost`, `conversions`. Convert cost from micros if the connector lands it in micros (Google Ads reports `cost_micros`, cost in GBP `= cost_micros / 1e6`). Add an `order_month` column (`date_trunc('month', search_date)`) so the dashboard Month filter can drive the tile, and an `order_month_label` (`to_char(order_month, 'YYYY-MM')`). Add a `store_id = 'isclinical'` constant for consistency with the rest of the Silver layer. Add a `brand_intent` classification derived from the search-term text, for example:
  ```sql
  case
    when lower(search_term) like '%is clinical%'
      or lower(search_term) like '%isclinical%'
      or lower(search_term) like '%is-clinical%'
      then 'branded'
    else 'non_branded'
  end as brand_intent
  ```
  Refine the branded patterns to also catch iS Clinical product names and common misspellings; validate the split against the PDF's 92.2% / 7.8% cost share before merging (see the Snowflake fallback SQL).
- **Create the Gold fact model `dbt/models/gold/fct_google_ads_search_terms.sql`.** Either pass Silver through (`select * from {{ ref('stg_google_ads__search_terms.sql') }}`) or aggregate to one row per `(order_month, brand_intent)` if a pre-aggregated grain is preferred for dashboard speed. Carry `brand_intent`, `clicks`, `cost`, `conversions`, `order_month`, `order_month_label`, `store_id`.
- **Add `dbt/models/gold/_schema.yml` entries for the new Gold model.** Declare a `brand_intent` dimension (optionally a `case` mapping `branded -> Branded`, `non_branded -> Non-branded` for display), the `order_month` / `order_month_label` dimensions, and metrics: `total_clicks` (`type: sum` on `clicks`), `total_cost` (`type: sum`, `format: gbp` on `cost`), `total_conversions` (`type: sum` on `conversions`). The "% of cost" column is a within-table share that does not aggregate additively, prefer a Lightdash table calculation (`total_cost / sum(total_cost)`) over a dbt metric.
- **Tests:** `not_null` on the primary key columns (`search_date` / `search_term` on Silver, `order_month` + `brand_intent` on the Gold fact if aggregated). `not_null` on `brand_intent` plus `accepted_values` with `values: ['branded', 'non_branded']`. `dbt_utils.accepted_range` with `min_value: 0` on `clicks`, `cost` and `conversions`.
- Run `cd dbt && dbt build --select stg_google_ads__search_terms+ fct_google_ads_search_terms+` and confirm all tests pass.

## Lightdash work
- Tile type: **table**. It sits on the iS Clinical KPI Report dashboard under the "Paid Media Performance" heading (PDF page 15), as the right-hand panel of that section, mirroring the PDF's "GOOGLE ADS, BRANDED VS NON-BRANDED" table. Place it in dashboard reading order after ticket `012` (Meta ads remarketing vs acquisition, the left-hand panel of the same PDF page) and before ticket `014` (CRM KPI strip, PDF page 16).
- Create `lightdash/charts/paid-search-shopping.yml` (one file per tile). The tile is a table chart on the `fct_google_ads_search_terms` explore, with:
  - the `brand_intent` dimension as the row grouping (two rows: branded, non-branded),
  - the `total_clicks`, `total_cost` and `total_conversions` metrics as columns,
  - one table calculation for **% of cost** (`total_cost / sum(total_cost)` over the table, formatted as a percentage, for example `92.2%`).
  - Before creating a new chart YAML, check `lightdash/charts/` for an existing Google Ads or paid-media table chart and adapt it instead of writing a new file from scratch. None is expected to exist (Google Ads has no model yet), so this will most likely be a new file.
  - Then update `lightdash/dashboards/kpi-report.yml` to add the tile.
- Mandatory: every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page 15 (Paid Media Performance)`.
- How the tile picks up the dashboard's Month filter: the dashboard Month filter is defined on `fct_orders_order_month_label`. The new `fct_google_ads_search_terms` explore must expose an `order_month_label` dimension (`to_char(order_month, 'YYYY-MM')`), identical in name to the field the dashboard filter targets, so Lightdash cross-applies the filter by matching field name via `tileTargets`. Confirm `order_month_label` is present on the explore before editing the YAML, and that the tile's `tileTargets` maps the dashboard Month filter onto `fct_google_ads_search_terms_order_month_label`.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the table.
- Assert it reproduces the April 2026 iS Clinical values from the "PDF reference" section above: the two brand-intent rows sum to total clicks **1,226**, total cost **£5,076**, total conversions **162**; the branded row reads ~1,209 clicks / ~£4,678 cost / 159 conversions / 92.2% of cost, and the non-branded row reads ~17 clicks / ~£397 cost / 3 conversions / 7.8% of cost.
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue (likely the `brand_intent` classification not matching the PDF's bucketing, or the table not scoped to the top 100 search terms by cost) or a known data-availability gap from section (c), and note the cause in the ticket. The most likely failure modes are (1) the branded pattern set missing a product name or misspelling, landing a term in the wrong bucket, and (2) forgetting the "top 100 search terms by cost" scope, which inflates clicks and cost above the PDF totals. Tune the `case` expression and the `qualify row_number() over (order by cost desc) <= 100` scope until the per-row totals match the PDF.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`). This runs the classification straight against Bronze so you can validate the brand-intent buckets before wiring dbt. Adjust the table and column names to whatever the Airbyte Google Ads connector actually landed (inspect `BRONZE_GOOGLE_ADS_ISCLINICAL` first; the search-term stream and its date / search-term / cost / clicks / conversions columns vary by connector version):
```sql
-- Step 1: inspect the schema to find the search-term stream and its column names.
-- show tables in schema HGI.BRONZE_GOOGLE_ADS_ISCLINICAL;
-- describe table HGI.BRONZE_GOOGLE_ADS_ISCLINICAL.<search_term_table>;

-- Step 2: reproduce the panel (replace <search_term_table>, <date_col>,
-- <search_term_col>, <cost_micros_col>, <clicks_col>, <conversions_col>).
with terms as (
    select
        <search_term_col> as search_term,
        <clicks_col>      as clicks,
        <cost_micros_col> / 1e6 as cost,
        <conversions_col> as conversions
    from HGI.BRONZE_GOOGLE_ADS_ISCLINICAL.<search_term_table>
    where <date_col> >= '2026-04-01' and <date_col> < '2026-05-01'
),
top_100 as (
    select *
    from terms
    qualify row_number() over (order by cost desc) <= 100
),
classified as (
    select
        case
            when lower(search_term) like '%is clinical%'
              or lower(search_term) like '%isclinical%'
              or lower(search_term) like '%is-clinical%'
                then 'branded'
            else 'non_branded'
        end as brand_intent,
        clicks,
        cost,
        conversions
    from top_100
)
select
    brand_intent,
    sum(clicks)                            as clicks,
    round(sum(cost), 0)                    as cost,
    round(sum(conversions), 0)             as conversions,
    round(100 * sum(cost) / sum(sum(cost)) over (), 1) as pct_of_cost
from classified
group by brand_intent
order by brand_intent;
-- expect two rows summing to clicks ~= 1226, cost ~= 5076, conversions ~= 162;
-- branded ~= 1209 clicks / 4678 cost / 159 conv / 92.2%, non_branded ~= 17 clicks / 397 cost / 3 conv / 7.8%,
-- matching the PDF page 15 panel. If totals run high, confirm the top-100-by-cost scope is applied.
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket introduces the **first Google Ads dbt models** (Bronze source `bronze_google_ads_isclinical`, Silver `stg_google_ads__search_terms`, Gold `fct_google_ads_search_terms`) and a new convention: a Google Ads `brand_intent` classification derived from the search-term text (`is clinical` / `isclinical` / `is-clinical` / product names / misspellings -> branded; else non_branded). Add `BRONZE_GOOGLE_ADS_ISCLINICAL` to the Snowflake schema list and the new models to the repo-structure / conventions sections of `CLAUDE.md`. Also note that the stale "Google Ads pending source-side fix" description on `fct_ad_spend` in `dbt/models/gold/_schema.yml` should be corrected, Google Ads is now live in Bronze and modelled by this ticket's new fact (it is a separate model from the Meta-only `fct_ad_spend`).
