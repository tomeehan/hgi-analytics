# Ticket generator: April 2026 KPI Report (iS Clinical) to Lightdash

This file is the **single source of truth** for producing tickets that rebuild the **iS Clinical brand section of the April 2026 KPI Report** PDF as a live Lightdash dashboard. A future Claude session reads this one file, walks the inventory in section (e), and writes one `tickets/NNN_<slug>.md` per row using the template in section (b).

The PDF reference lives at `reference/april_2026_kpi_report.pdf`. Treat its numbers as authoritative: each ticket builds one tile and verifies its value against the PDF.

> **Note (2026-05-20):** The dashboard is scoped to iS Clinical only. The guiding mental model is "the iS Clinical version of the April 2026 KPI Report PDF": a single-brand dashboard that reproduces the report's iS Clinical brand section plus the iSC-scoped headline KPIs. There is no multi-brand framing and no dashboard Brand filter, only a Month filter.

---

## (a) Project preamble (copy verbatim into every ticket)

> **Project (one paragraph):** This repo is `hgi-analytics`. We ingest Shopify, Klaviyo, Meta, GA4, Google Ads, Cin7 and Prospect CRM into Snowflake via Airbyte, transform with dbt (Bronze, Silver, Gold), and serve dashboards from Lightdash. Full project README is `CLAUDE.md` in the repo root. Read it first if you have not seen this project before. Lightdash charts and dashboards are managed as code (YAML in `lightdash/charts/` and `lightdash/dashboards/`); read the "Lightdash dashboards-as-code" section of `CLAUDE.md` before touching any tile.
>
> **Wider goal of these tickets:** Build the **iS Clinical KPI Report** dashboard in Lightdash, the iS Clinical version of the April 2026 KPI Report PDF (`reference/april_2026_kpi_report.pdf`). The PDF is treated as numerically authoritative. Each ticket builds one tile on the **iS Clinical KPI Report** dashboard and verifies the April 2026 iS Clinical number against the PDF. This is a single-brand dashboard: there is no Brand filter, only a Month filter.
>
> **The generator that produced this ticket:** `tickets/_ticket_generator.md`. Read sections (c) data availability map and (d) filter design before starting if you have not touched these tickets before.
>
> **Context window discipline:** Spawn subagents (Explore for codebase searches, Plan for design questions, general purpose for multi step research) so this session's context stays focused on the implementation. Do not foreground read every file linked from this ticket. Delegate.
>
> **This ticket is fully autonomous.** You are responsible for taking the work from Triage all the way to merged, deployed and verified. Do not stop for human approval at any intermediate step. The end state is: PR merged to main, `lightdash_deploy.yml` green on main (it auto-runs `lightdash deploy` then `lightdash upload --force`), the dashboard tile verified against the PDF number, and the Basecamp card moved to Done with a verification comment.

## (b) Ticket template (use verbatim, fill the bracketed placeholders)

````markdown
# NNN: <Metric Name>

> {project preamble from generator section (a), pasted verbatim}

## End to end workflow (run this top to bottom, autonomously)

1. **Claim the card on Basecamp.** Using the `basecamp` skill, find this ticket on the Data Engineering card table (account `5735756`, bucket `46863097`, card table `9778948512`), and move it from **Triage** to **In progress**.
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-NNN-<slug>`. (Always rebase before branching, per the project's PR workflow.)
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
   - `git push -u origin ticket-NNN-<slug>`.
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
- Page <N>, section "<Section title>".
- April 2026 value (iS Clinical): **<exact number from PDF>**.

## Metric definition
- Plain English description of what the metric counts.
- Source of truth chain per the PDF appendix (Shopify, GA4, Meta, Google Ads, Klaviyo).
- Filter behaviour: how the tile responds to the dashboard's **Month** filter.

## Data dependencies
- Bronze sources needed (with current status from generator section (c): ok loaded, blocked on Airbyte, or partial).
- Silver and Gold models that already cover this (file paths under `dbt/models/`).
- New Silver or Gold models or columns required, if any.

## dbt work
- Exact models to add or modify, with rationale.
- Tests to add (`not_null` and `unique` on keys, range tests on numeric outputs).
- If none required, write "no dbt changes needed".

## Lightdash work
- Tile type (big number, bar chart, table, pie, markdown) and where on the iS Clinical KPI Report dashboard it sits (which row, under which heading, mirroring the PDF page order).
- The `lightdash/charts/<slug>.yml` file to create or adapt (one per tile), plus the update to `lightdash/dashboards/kpi-report.yml` to place the tile.
- Mandatory: every chart and dashboard YAML file created or edited must have, as its first line, the comment `# Source: April 2026 KPI Report, page <N> (<section title>)`.
- Before creating a new chart YAML, check `lightdash/charts/` for an existing chart that already fits and adapt it instead.
- How the tile picks up the dashboard's Month filter: the underlying explore **must** expose `order_month` (or an equivalent month-truncated date dimension), matching the field used by `lightdash/dashboards/kpi-report.yml`. Confirm this before editing the YAML.

## Preview verification
Verify the tile in the preview project (step 5 of the workflow) against the PDF number:
- After `lightdash upload --force --validate --project <preview-uuid>`, open the preview URL.
- With the Month filter set to April 2026, read the tile value.
- Assert it equals the April 2026 iS Clinical value stated in the "PDF reference" section above.
- If it does not match, do not merge: reproduce the number with the Snowflake fallback SQL below to find out whether the gap is a dbt/model issue or a known data-availability gap from section (c), and note the cause in the ticket.

## Snowflake fallback SQL
The ground-truth check. Reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
<copy pasteable SQL>
```

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section).
````

## (c) Data availability map (as of 2026-05-20, verified against Snowflake)

The PDF assumes every source is fully populated. The repo is not yet. Bake this into every ticket's "Data dependencies" section. This batch is iS Clinical only, so only iS Clinical sources are listed.

> **Known data gap: the iS Clinical Shopify Airbyte sync is degraded.** The iS Clinical Shopify source authenticates with a **rotating OAuth token** (not a static custom-app token). The token fails mid-sync, and when it does Airbyte silently drops scattered records rather than erroring loudly. The result is that Bronze runs roughly **2.6% short** for a full month. For April 2026, Bronze holds **1,047 orders** against the **1,075** stated in the PDF. Every Shopify-derived ticket (revenue, orders, AOV, customer mix) must note this gap explicitly in its "Data dependencies" section and link the prerequisite "fix iS Clinical Shopify sync" data-engineering ticket. The PDF figure is authoritative; the live tile will read slightly low until the sync is fixed.

### Shopify

| Brand | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_SHOPIFY_ISCLINICAL` | Degraded: rotating OAuth token fails mid-sync and silently drops scattered records, Bronze runs ~2.6% short per month (April 2026: 1,047 orders ingested vs 1,075 in the PDF). See the note above. |

### Klaviyo

| Account | Bronze schema | Status |
|---|---|---|
| iS Clinical (DTC) | `BRONZE_KLAVIYO_ISCLINICAL` | Live |

> Klaviyo CRM tiles (CRM revenue, campaign and flow revenue, open and click rates, subscriber growth) must be built from the raw `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` table (5.9M rows, fully populated). Klaviyo's pre-aggregated reporting streams (`campaign_values_reports`, `flow_series_reports`) are deliberately not synced (lean stream selection), so any legacy Gold model that depended on them is empty. Engagement events (Received, Opened, Clicked Email) carry `$message`, `$campaign`, `$flow` and `Campaign Name` in `event_properties`; Placed Order events carry `$value` but no campaign or flow, so campaign and flow revenue is an attribution computation: attribute each Placed Order's `$value` to the campaign or flow of that profile's most recent email engagement within a 5-day window. Open and click rates come straight from the Received, Opened and Clicked Email event counts, no attribution join needed.

### Meta

| Ad account | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_META_ISCLINICAL` | Live |

### GA4 (Google Analytics)

| Brand | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` | Live: 10 reports loaded (channel grouping, source/medium, conversions, events, demographics, pages, e-commerce purchases, daily active users, website overview) |

### Google Ads

| Brand | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_GOOGLE_ADS_ISCLINICAL` | Live: full Airbyte stream set (campaign, ad group, keyword, search query, shopping product, geo, age/gender, etc) |

### Cin7 and Prospect CRM
Both live and out of scope for this batch (the PDF report doesn't reference them).

### Implication for tickets

- **Shopify tickets** (revenue, orders, AOV, customer mix) can be built today. The ~2.6% iSC sync gap will surface at verification; the ticket must note it explicitly and link the "fix iS Clinical Shopify sync" prerequisite ticket.
- **Klaviyo, Meta, GA4 and Google Ads tickets** can all be built and verified for iS Clinical today. Every source needed for the iS Clinical brand section is live.

## (d) Filter design (installed by ticket 001, reused by everything downstream)

This is a single-brand dashboard. There is **no Brand filter**. The dashboard layout mirrors the iS Clinical brand section of the PDF: each metric tile is always on screen, and the Month filter scopes every tile to one calendar month.

### Month filter (dashboard level, the only filter)
- Label: **"Month"**.
- Underlying field: `fct_orders_order_month_label` on the `fct_orders` explore (matches the filter already present in `lightdash/dashboards/kpi-report.yml`).
- Default value: **`2026-04`**, displayed as "April 2026".
- For sources that don't already carry a month concept (Klaviyo, Meta, GA4, Google Ads), the Silver staging model adds `date_trunc('month', <event_timestamp>) as order_month` so the single dashboard filter drives every tile. Where a tile uses a different explore, it cross-applies the Month filter via `tileTargets` onto the matching field name.

### Tile compliance
Every tile produced by these tickets must expose `order_month` (or the equivalent month-truncated dimension) in its underlying explore. If it does not, the dashboard Month filter silently won't apply, breaking verification. Confirm this in the "Lightdash work" section before editing the YAML.

## (e) Ticket inventory

Numbering follows reading order through the PDF, 001 to 020. The "iSC April target" column is the verification target each ticket must hit with the Month filter on April 2026; entries marked "verify against PDF" must be read off the PDF by the generating subagent (rule 2). Exact PDF page numbers are confirmed per ticket by the generating subagent (rule 2): the iS Clinical brand section spans roughly PDF pages 12 to 19, and the cover page is page 1.

| # | slug | tile | iSC April target |
|---|---|---|---|
| 001 | shopify_revenue | iS Clinical Shopify Revenue (big number). Also rescopes the dashboard, see the note below | £144,532 |
| 002 | shopify_orders | iS Clinical Shopify Orders (big number) | 1,075 |
| 003 | meta_spend | iS Clinical Meta Spend (big number) | £7,657 |
| 004 | klaviyo_revenue | iS Clinical Klaviyo Revenue (big number) | verify against PDF |
| 005 | revenue_channel_attribution_kpis | Revenue & channel attribution KPI strip | revenue £144,532, GA-attributed £73,808, AOV £134.45 |
| 006 | channel_breakdown_table | Channel breakdown table (GA4 channels) | verify against PDF |
| 007 | traffic_conversion_kpi_strip | Traffic & conversion KPI strip | 15,682 sessions, 13,300 users, 3.53% CVR |
| 008 | top_traffic_sources_by_sessions | Top GA4 traffic sources by sessions | verify against PDF |
| 009 | top_converting_sources_by_rps | Top GA4 converting sources by RPS | verify against PDF |
| 010 | pr_media_highlights | PR & media highlights (top GA4 referrers) | verify against PDF |
| 011 | customer_mix_aov_split | Customer mix & AOV split (new vs returning) | 385 new / 690 returning orders |
| 012 | meta_remarketing_vs_acquisition | Meta ads: remarketing vs acquisition | £7,657 spend, 406 purchases, 7.46x ROAS |
| 013 | paid_search_shopping | Paid search / shopping (Google Ads branded vs non-branded) | verify against PDF |
| 014 | crm_kpi_strip | CRM KPI strip | CRM rev £64,885, campaign £50,667, flow £14,218 |
| 015 | top_performing_campaigns | Top performing Klaviyo campaigns | verify against PDF |
| 016 | top_performing_flows | Top performing Klaviyo flows | verify against PDF |
| 017 | subscriber_growth_totals | 12-month subscriber growth totals | verify against PDF |
| 018 | subscriber_growth_monthly_bar_chart | 12-month subscriber growth monthly bar chart | verify against PDF |
| 019 | subscriber_growth_monthly_table | 12-month subscriber growth monthly table | verify against PDF |
| 020 | methodology_data_sources | Methodology & data sources note (markdown tile) | n/a |

> **Ticket 001 rescopes the dashboard.** In addition to building the iS Clinical Shopify Revenue tile, ticket 001 rescopes the existing `lightdash/dashboards/kpi-report.yml` into the iS Clinical KPI Report:
> - rename the dashboard to "iS Clinical KPI Report",
> - drop the disabled Brand filter (the `fct_orders_store_id` dimension filter) entirely,
> - remove the four cross-brand tiles: `per-brand-breakdown`, `meta-spend-share-by-brand`, `ga4-revenue-share-by-brand`, `april-at-a-glance`,
> - keep the Month filter on `fct_orders_order_month_label`, default `2026-04`.
>
> Tickets 002 to 020 each append exactly one tile to the rescoped dashboard.

## (f) Generation rules (read this before mass producing tickets)

A future Claude session producing tickets 002 through 020 should follow these rules:

1. **One subagent per ticket.** Spawn a general purpose subagent for each ticket; give it this generator file as context plus the row in section (e). The subagent reads, writes one ticket file, returns. Parallelise within batches of 3 or 4 so context stays bounded.

2. **Verify each PDF reference before writing.** The subagent must open the PDF (Read tool with `pages:`) at the relevant page and confirm the iS Clinical April value before writing it into the ticket. Do not trust the inventory blindly. The PDF wins if they disagree, and the inventory is updated. Confirm the exact page number too: the inventory only gives an approximate range (iS Clinical brand section ~pages 12 to 19).

3. **Verify the data path before writing the Lightdash work section.** Before writing "tile reads from explore X", `grep` for the relevant Gold model in `dbt/models/gold/` and confirm the columns exist. If the metric requires a model that does not exist, the ticket's "dbt work" section lists creating it. Do not pretend it exists.

4. **Check the data availability map.** If section (c) marks the underlying source as blocked, partial or degraded, the ticket's "Data dependencies" section must say so explicitly and link a prerequisite ticket (or describe the prerequisite if no such ticket exists yet). Every Shopify ticket must carry the iS Clinical sync-gap note.

5. **Mirror the PDF layout.** A tile maps to one visual unit on the PDF. KPI strips that show several numbers in one row on the PDF are one tile and one ticket.

6. **Push every ticket to Basecamp as HTML.** This is the deliverable: a card in the Triage column whose body renders correctly in Basecamp. The local `tickets/NNN_<slug>.md` file stays in the repo as a reviewable / recoverable copy, but the Basecamp card content must be **HTML, not Markdown**.

   Basecamp's CLI claims to convert Markdown to HTML on the `--content` flag, but empirically it only auto-links URLs. Headings (`#`), bold (`**`), tables, fenced code blocks, blockquotes, ordered lists, all stay as raw characters. So convert with `pandoc` before pushing:

   ```bash
   pandoc -f gfm -t html tickets/NNN_<slug>.md > /tmp/NNN.html
   basecamp card --title "NNN: Title" --content "$(cat /tmp/NNN.html)" --column 9778948514 --in 46863097 --json
   ```

   GFM (`-f gfm`) preserves tables, task lists, fenced code blocks, and strikethrough, all of which the tickets use. Verify the card renders by opening it in Basecamp before moving on (or as part of bulk verification at the end).

7. **Keep the index up to date.** Maintain `tickets/README.md` as the running index (ticket number, title, status, blockers). Add each ticket to it as you write it.

8. **Don't free write.** Use the template in section (b) verbatim. The preamble, the workflow section, the verification block, all copy paste. Variability lives only in the bracketed placeholders.

9. **No em dashes.** The user's global writing style rule disallows em dashes. Use commas, full stops, colons, or parentheses instead. The card title uses a colon, for example `001: iS Clinical Shopify Revenue`.

10. **Wrap `<placeholder>` text in backticks** (`` `<slug>` `` or fenced code blocks). Even after the pandoc-to-HTML pass, unbacktick'd `<like-this>` text gets eaten by Basecamp's renderer as a stray HTML tag. Backticks make pandoc emit `<code>&lt;like-this&gt;</code>` which renders correctly.

11. **If you update a card (re-push), use `basecamp cards update <id> --content "$(cat /tmp/NNN.html)" --in 46863097 --json`.** Updates are idempotent; safe to re-run after fixing a markdown source.

12. **Every chart and dashboard YAML file carries a Source comment.** Any `lightdash/charts/<slug>.yml` or `lightdash/dashboards/<slug>.yml` an executor creates or edits must have, as its first line, a comment in the exact form `# Source: April 2026 KPI Report, page <N> (<section title>)`. The ticket's "Lightdash work" section must state this requirement.

## (g) Open questions and known gaps

- **The iS Clinical Shopify Airbyte sync is degraded (main blocker).** It authenticates with a rotating OAuth token that fails mid-sync; when it does, Airbyte silently drops scattered records instead of erroring. Bronze ends up ~2.6% short per month (April 2026: 1,047 orders ingested vs 1,075 in the PDF). Shopify-derived tiles (revenue, orders, AOV, customer mix) will read slightly low until this is fixed. A separate data-engineering ticket should fix the token; every Shopify ticket links it as a prerequisite and the PDF figure stays authoritative.
- **GA4 and Google Ads are live for iS Clinical.** Every per-section tile in the iS Clinical brand inventory (channel attribution, traffic/conversion, paid search/shopping) is buildable and verifiable today; there is no GA4 or Google Ads connection blocker for this batch.
