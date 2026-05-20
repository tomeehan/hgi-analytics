# 020: Methodology & data sources note

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
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-020-methodology_data_sources`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-020-methodology_data_sources`.
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
- Page 31, section "APPENDIX, Methodology & data sources" (the "SOURCE-OF-TRUTH HIERARCHY" table). The cover page, page 1, also carries a condensed "Data sources used" strip that this tile draws on.
- April 2026 value (iS Clinical): **n/a, this is a static informational tile with no numeric metric**. There is no April number to verify. Verification is purely that the tile renders the methodology text correctly (see the "Preview verification" section).

## Metric definition
- This tile has no numeric metric. It is a static markdown note that reproduces the report's source-of-truth hierarchy and attribution methodology, so a dashboard viewer can see, at a glance, which source backs each tile and what attribution window each source uses. It is the dashboard equivalent of the PDF's appendix page.
- Source of truth chain per the PDF appendix (this is the content the tile reproduces verbatim, from page 31's "SOURCE-OF-TRUTH HIERARCHY" table and page 1's "Data sources used" strip):
  - **Shopify** provides order count, true revenue, AOV and customer order history. Attribution window: **source of truth (no attribution)**. Shopify is authoritative for revenue and orders.
  - **GA4** provides channel/source revenue, sessions, CVR and customer mix. Attribution window: **last non-direct click**.
  - **Meta** provides spend, impressions, clicks, ROAS and ad-set level performance. Attribution window: **7-day click + 1-day view (Meta default)**.
  - **Google Ads** provides spend, clicks, conversions, search terms and ROAS. Attribution window: **1-day click + 1-day view**.
  - **Klaviyo** provides campaign + flow revenue, opens, clicks and profile counts. Attribution window: **Placed Order, 5-day attribution window**.
- Filter behaviour: the tile is a static dashboard markdown tile and **does not respond to the Month filter**. Its content is fixed methodology text, identical for every month. Because it is a markdown tile and not a saved chart, it has no underlying explore and the `order_month` requirement from generator section (d) does not apply.

## Data dependencies
- Bronze sources needed: **none**. This tile reads no data from Snowflake. It is pure markdown content typed into the dashboard YAML.
- Silver and Gold models that already cover this: **none, and none are needed**. No `dbt/models/` file backs this tile.
- New Silver or Gold models or columns required: **none**.
- No data-availability gap from generator section (c) applies, because the tile queries no source. The iS Clinical Shopify sync-gap note does not apply here (this is not a Shopify-derived tile, it is a static note). That said, the tile's text describes Shopify as the source of truth, which is consistent with how the rest of the dashboard treats it.

## dbt work
- **No dbt changes needed.** This tile is a static Lightdash markdown tile with no backing model, no metric and no SQL. There is nothing to add to `dbt/models/`, no tests to write, and no `dbt build` to run for this ticket.

## Lightdash work
- Tile type: **markdown** (a Lightdash dashboard markdown tile, not a saved chart). It sits at the **bottom of the iS Clinical KPI Report dashboard**, as the final tile, mirroring the PDF where "Methodology & data sources" is the closing appendix page (page 31). It is full-width and reads as a closing footnote to the dashboard.
- **No `lightdash/charts/<slug>.yml` file is created or edited.** A markdown tile is not a saved chart: it has no chart YAML, no explore, no query. The tile content lives entirely inside the dashboard YAML. So the only file touched is `lightdash/dashboards/kpi-report.yml`.
- Update `lightdash/dashboards/kpi-report.yml` to append one tile of type `markdown` (Lightdash's dashboard tile schema supports a `markdown` tile type alongside `saved_chart` and `loom`). The tile's `properties` carry a `title` (for example "Methodology & data sources") and a `content` field holding the markdown body. Reproduce the source-of-truth hierarchy as a markdown table inside `content`:

  | Source | What it provides | Attribution window |
  |---|---|---|
  | Shopify | Order count, true revenue, AOV, customer order history | Source of truth (no attribution) |
  | GA4 | Channel/source revenue, sessions, CVR, customer mix | Last non-direct click |
  | Meta | Spend, impressions, clicks, ROAS, ad-set level performance | 7-day click + 1-day view (Meta default) |
  | Google Ads | Spend, clicks, conversions, search terms, ROAS | 1-day click + 1-day view |
  | Klaviyo | Campaign + flow revenue, opens, clicks, profile counts | Placed Order, 5-day attribution window |

  Confirm whether the live Lightdash version's markdown tile renders GitHub-flavoured markdown tables. If it does not, fall back to a definition-list / bulleted layout that conveys the same source -> what-it-provides -> attribution-window mapping.
- **Mandatory:** the dashboard YAML file edited (`lightdash/dashboards/kpi-report.yml`) must have, as its first line, the comment `# Source: April 2026 KPI Report, page 31 (APPENDIX, Methodology & data sources)`. If that file already carries a `# Source:` first-line comment from an earlier ticket (001 onwards), leave the existing comment in place rather than adding a second one (it is a per-file comment, not a per-tile one); the page-31 citation for this tile is recorded here in the ticket and in the commit message.
- Before editing, check `lightdash/charts/` only to confirm there is **no** existing chart to adapt: there is not, because this is a markdown tile, not a chart. This step is a no-op for this ticket, recorded here for completeness against the generator's "check for an existing chart first" rule.
- How the tile picks up the dashboard's Month filter: it does not, and it should not. A markdown tile has no explore and exposes no `order_month` dimension, so the generator section (d) `order_month` requirement does not apply. The tile content is month-agnostic methodology text. When adding the tile to `kpi-report.yml`, do **not** add a `tileTargets` entry for it: it is intentionally outside the Month filter's scope.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow). There is **no PDF number to verify**, so verification here is content and rendering only:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- Confirm the markdown tile renders at the bottom of the iS Clinical KPI Report dashboard, full-width, with the title "Methodology & data sources".
- Confirm the source-of-truth table renders with all five rows (Shopify, GA4, Meta, Google Ads, Klaviyo) and that each row's "Attribution window" cell matches the PDF appendix wording in the "Metric definition" section above (Shopify = source of truth/no attribution, GA4 = last non-direct click, Meta = 7-day click + 1-day view, Google Ads = 1-day click + 1-day view, Klaviyo = Placed Order, 5-day window).
- Confirm the Month filter does **not** affect this tile (changing the Month filter leaves the tile unchanged, as expected for a static note).
- If the markdown table does not render cleanly, switch to the bulleted fallback layout described in "Lightdash work" and re-preview. There is no Snowflake number to reconcile, so there is no merge-blocking numeric mismatch for this ticket.

## Snowflake fallback SQL
There is **no Snowflake fallback SQL for this ticket**. This tile has no numeric metric and reads no data from Snowflake, so there is nothing to reproduce from the warehouse. The "ground-truth check" for this tile is the PDF appendix text itself (`reference/april_2026_kpi_report.pdf`, page 31), which the tile reproduces verbatim. The ground truth is documentation accuracy, not a query result.

```sql
-- Not applicable: this is a static markdown tile with no backing model and no metric.
-- Verification is by reading the tile against PDF page 31, not by querying Snowflake.
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section). This ticket introduces no new source, schema or role. It does, however, establish a small convention worth recording: the iS Clinical KPI Report dashboard ends with a static methodology markdown tile that documents the source-of-truth hierarchy. If `CLAUDE.md`'s Lightdash section does not already note that dashboards can carry static markdown tiles (no chart YAML, content lives in the dashboard YAML), add a one-line note so future tickets do not look for a missing chart file. No "undecided" item in `CLAUDE.md` is resolved by this ticket.
