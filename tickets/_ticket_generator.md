# Ticket generator: April 2026 KPI Report to Lightdash

This file is the **single source of truth** for producing tickets that rebuild the **April 2026 KPI Report** PDF as a live Lightdash dashboard. A future Claude session reads this one file, walks the inventory in section (e), and writes one `tickets/NNN_<slug>.md` per row using the template in section (b).

The PDF reference lives at `reference/april_2026_kpi_report.pdf`. Treat its numbers as authoritative: each ticket builds one tile and verifies its value against the PDF.

---

## (a) Project preamble (copy verbatim into every ticket)

> **Project (one paragraph):** This repo is `hgi-analytics`. We ingest Shopify, Klaviyo, Meta, GA4, Google Ads, Cin7 and Prospect CRM into Snowflake via Airbyte, transform with dbt (Bronze, Silver, Gold), and serve dashboards from Lightdash. Full project README is `CLAUDE.md` in the repo root. Read it first if you have not seen this project before.
>
> **Wider goal of these tickets:** Recreate the **April 2026 KPI Report** PDF (`reference/april_2026_kpi_report.pdf`) as a live, brand and month filterable dashboard in Lightdash. The PDF is treated as numerically authoritative. Each ticket builds one tile on the **Group Overview** dashboard and verifies the April 2026 number against the PDF.
>
> **The generator that produced this ticket:** `tickets/_ticket_generator.md`. Read sections (c) data availability map and (d) filter design before starting if you have not touched these tickets before.
>
> **Context window discipline:** Spawn subagents (Explore for codebase searches, Plan for design questions, general purpose for multi step research) so this session's context stays focused on the implementation. Do not foreground read every file linked from this ticket. Delegate.
>
> **This ticket is fully autonomous.** You are responsible for taking the work from Triage all the way to merged, deployed, migration run, and verified via the Lightdash API. Do not stop for human approval at any intermediate step. The end state is: PR merged to main, deploy action green, migration script applied, dashboard tile value verified against the PDF by API call, Basecamp card moved to Done with a verification comment.

## (b) Ticket template (use verbatim, fill the bracketed placeholders)

````markdown
# NNN: <Metric Name>

> {project preamble from generator section (a), pasted verbatim}

## End to end workflow (run this top to bottom, autonomously)

1. **Claim the card on Basecamp.** Using the `basecamp` skill, find this ticket on the Data Engineering card table (account `5735756`, bucket `46863097`, card table `9778948512`), and move it from **Triage** to **In progress**.
2. **Branch.** `git fetch origin && git checkout main && git pull --rebase && git checkout -b ticket-NNN-<slug>`. (Always rebase before branching, per the project's PR workflow.)
3. **Implement.**
   - dbt changes (if any): edit the models listed below, then run `cd dbt && dbt build --select <model>+` and confirm tests pass.
   - Lightdash migration: scaffold with `bin/new-lightdash-migration <slug>`, edit per the "Lightdash work" section, dry run with `python3 lightdash/migrations/<file> --dry-run`, and only proceed once the planned API calls look right.
4. **Commit + PR.**
   - `git add -p && git commit` (commit conventions in `CLAUDE.md`: no em dashes, no co-author trailer, no "Generated with Claude Code" footer).
   - `git push -u origin ticket-NNN-<slug>`.
   - `gh pr create` with a body that includes the **Post deploy ops** line verbatim (see template at the bottom of this ticket).
5. **Self merge on green CI.**
   - Wait around 10 seconds, then `gh pr checks <pr-number> --watch` until CI is green.
   - `gh pr merge --rebase --delete-branch`. Never push to main directly. Never use `--no-verify` or skip hooks.
6. **Watch the deploy.**
   - The `lightdash_deploy.yml` workflow fires automatically on push to main. Poll with `gh run list --workflow=lightdash_deploy.yml --limit 1 --json status,conclusion,databaseId --jq '.[0]'`, or `gh run watch <run-id>`. Wait until `status=completed, conclusion=success`.
7. **Run the migration.**
   - `python3 lightdash/migrations/<file>` (no `--dry-run` this time). The migration mutates Lightdash state via the API and should print one line per API call.
8. **Verify via the Lightdash API (not the browser).**
   - Import the helpers from `lightdash/migrations/_lib.py` (or curl with auth from `.env`) and:
     - `GET /api/v1/dashboards/a8941b36-5393-43fb-9714-cd7edb582803` to confirm the new tile UUIDs are present in `tiles[]`.
     - For each new chart, `POST /api/v1/saved/<chart-uuid>/results` with the Brand=All / Month=April-2026 filter combo, and assert the returned value equals the expected April number from this ticket.
     - Repeat the API query with Month=March-2026 to capture the March value (needed for the Basecamp comment, and proves the month filter works end to end).
9. **Close the loop on Basecamp.**
   - Add a comment to the card with:
     - the merged PR URL,
     - the verified April and March values (from step 8),
     - the dashboard tile UUIDs you just created,
     - any caveats or known gaps (especially if the live number does not match the PDF, link the prerequisite ticket).
   - Move the card from **In progress** to **Done**.
10. **Pick up the next ticket.** Look at Basecamp Triage. If there is another card from this batch (named `NNN: ...`), pick the lowest numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page <N>, section "<Section title>".
- April 2026 value: **<exact number from PDF>**.
- March 2026 value (for filter change validation): <number, or "not in PDF, capture at verification time via the API call in step 8 and write into the Basecamp comment">.

## Metric definition
- Plain English description of what the metric counts.
- Source of truth chain per the PDF appendix on page 31 (Shopify, GA4, Meta, Google Ads, Klaviyo).
- Filter behaviour: how the tile responds to the dashboard's **Brand** and **Month** filters.

## Data dependencies
- Bronze sources needed (with current status from generator section (c): ok loaded, blocked on Airbyte, or partial).
- Silver and Gold models that already cover this (file paths under `dbt/models/`).
- New Silver or Gold models or columns required, if any.

## dbt work
- Exact models to add or modify, with rationale.
- Tests to add (`not_null` and `unique` on keys, range tests on numeric outputs).
- If none required, write "no dbt changes needed".

## Lightdash work
- Tile type (big number, bar chart, table, pie, markdown) and where on the Group Overview dashboard it sits (which row, under which heading, mirroring the PDF page order).
- The migration filename to create via `bin/new-lightdash-migration <slug>` (produces `lightdash/migrations/YYYYMMDD_HHMMSS_<slug>.py`).
- How the tile picks up the dashboard's Brand and Month filters: the underlying explore **must** expose `store_id` and `order_month` (or an equivalent month truncated date dimension). Confirm this before writing the migration.

## API verification snippet
Embed a Python snippet that runs in step 8 of the workflow above. Pattern:
```python
import sys
sys.path.insert(0, "lightdash/migrations")
from _lib import api

DASH = "a8941b36-5393-43fb-9714-cd7edb582803"
EXPECTED_APRIL = <number>

dash = api("GET", f"/dashboards/{DASH}")
tile_uuids = [t["uuid"] for t in dash["tiles"]]
print("tiles on dashboard:", tile_uuids)

# Replace <chart-uuid> after the migration prints it
results = api("POST", "/saved/<chart-uuid>/results", body={
    "filters": {"dimensions": [
        {"target": {"fieldId": "fct_orders_order_month"}, "operator": "equals", "values": ["2026-04-01"]},
    ]},
})
got = results["rows"][0]["fct_orders_total_price_sum"]["value"]["raw"]  # adjust field id
assert got == EXPECTED_APRIL, f"April mismatch: got {got}, expected {EXPECTED_APRIL}"
print(f"April OK: {got}")
```
Adjust the field IDs and the response path to match your migration. If the tile uses a chart that does not exist yet, use the `POST /api/v1/projects/<projectUuid>/explores/<exploreId>/runQuery` endpoint to run an ad hoc query against the explore instead.

## Snowflake fallback SQL
If the API path fails or the answer disagrees with the PDF, reproduce the number directly from Snowflake (via `snow sql -c hgi`):
```sql
<copy pasteable SQL>
```

## Post deploy ops (paste into the PR description)
> Post deploy ops: wait for `lightdash_deploy.yml` to finish (the bot watches this in step 6), then run `python3 lightdash/migrations/YYYYMMDD_HHMMSS_<slug>.py` (step 7).
(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed
If this ticket introduces a new source, schema, role, convention, or resolves something previously marked undecided in `CLAUDE.md`, update `CLAUDE.md` in the same PR (per the "Keeping this file current" section).
````

## (c) Data availability map (as of 2026-05-13, verified against Snowflake)

The PDF assumes every source is fully populated. The repo is not yet. Bake this into every ticket's "Data dependencies" section.

### Shopify (per store Bronze counts, all time)

| Store | Bronze schema | Total Bronze orders | Earliest order | April 2026 orders | April 2026 gross | PDF April orders | PDF April £ | Status |
|---|---|---:|---|---:|---:|---:|---:|---|
| Revitalash | `BRONZE_SHOPIFY_REVITALASH` | 5,578 | 2026-02-26 | 2,637 | £263,317 | 2,669 | £266,908 | Partial: minor gap of around 32 orders / £3,591 |
| iS Clinical | `BRONZE_SHOPIFY_ISCLINICAL` | 175 | 2026-02-26 | 29 | £3,392 | 1,075 | £144,532 | Blocked: Airbyte sync only goes back around 10 weeks; needs full historical backfill |
| Deese PRO | `BRONZE_SHOPIFY_DEESE_PRO` | 3,233 | 2019-01-24 | 20 | £13,731 | 20 | £13,731 | Live: matches PDF exactly |
| Geske | `BRONZE_SHOPIFY_GESKE` | schema is empty / no `ORDERS` table | n/a | n/a | n/a | n/a | n/a | Blocked: Airbyte connection created but not synced |
| Harpar Grace Intl | not declared as a source | n/a | n/a | n/a | n/a | 27 | £3,157 | Blocked: harpargrace.com Shopify not connected at all |

**Combined April 2026 Shopify revenue today:** £279,895 across the loaded stores. PDF target: £428,328 (combined incl HGI) or £425,171 (excl HGI). The current £145k gap is dominated by the iS Clinical sync gap.

### Klaviyo

| Account | Bronze schema | Status |
|---|---|---|
| iS Clinical (DTC) | `BRONZE_KLAVIYO_ISCLINICAL` | Live |
| Deese PRO | `BRONZE_KLAVIYO_DEESE_PRO` | Live |
| Revitalash | `BRONZE_KLAVIYO_REVITALASH` | Live |
| Harper Grace (B2B) | `BRONZE_KLAVIYO_HARPER_GRACE` | Partial: connection emits records but no destination tables get written (see `airbyte/README.md`) |
| Geske | `BRONZE_KLAVIYO_GESKE` | Blocked: schema exists, no sync configured |

### Meta

| Ad account | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_META_ISCLINICAL` | Live |
| Deese PRO | `BRONZE_META_DEESE_PRO` | Live |
| Revitalash | `BRONZE_META_REVITALASH` | Live |

### GA4 (Google Analytics)

| Brand | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_GOOGLE_ANALYTICS_ISCLINICAL` | Live: 10 reports loaded (channel grouping, source/medium, conversions, events, demographics, pages, e-commerce purchases, daily active users, website overview), fresh to 2026-05-05 |
| Revitalash | not declared | Blocked: not connected |
| Deese PRO | not declared | Blocked: not connected |
| Harpar Grace Intl | not declared | Blocked: not connected |

### Google Ads

| Brand | Bronze schema | Status |
|---|---|---|
| iS Clinical | `BRONZE_GOOGLE_ADS_ISCLINICAL` | Live: full Airbyte stream set (campaign, ad group, keyword, search query, shopping product, geo, age/gender, etc) |
| Deese PRO | `BRONZE_GOOGLE_ADS_DEESE_PRO` | Partial: schema exists, no campaign-stats tables under the expected suffix yet (different ad account) |
| Revitalash | not declared | Blocked: not connected (PDF page 7 explicitly says "no Adspirer for RL", but we still need Google Ads for branded vs non-branded reporting) |

### Cin7 and Prospect CRM
Both live and out of scope for this batch (the PDF report doesn't reference them).

### Implication for tickets

- **Shopify only tickets** (revenue, orders, AOV, customer mix) can be built today; the iSC gap will surface in verification and the ticket should note it explicitly and link a sibling "fix iSC Shopify sync" ticket.
- **Klaviyo and Meta tickets** can be built for all live brands today.
- **GA4 and Google Ads tickets** can only be verified for iSC today. For other brands the tile will show no data until the Airbyte connections land. List the connection ticket as a dependency in each such ticket.

## (d) Filter design (installed by ticket 001, reused by everything downstream)

The dashboard layout mirrors the PDF: each metric tile is always on screen, the Brand filter does not switch the view, it only filters the data. Selecting "Revitalash" makes the iS Clinical tile show £0, it does not hide it.

### Brand filter (dashboard level)
- Label shown to users: **"Brand"**.
- Drop down values: **All**, **Revitalash**, **iS Clinical**, **Deese PRO**, **Geske** (add "Harpar Grace Intl" when its Shopify store is connected).
- Underlying field: `store_id` on every Silver and Gold model that has it.
- Slug to display name mapping:
  - `revitalash` displays as "Revitalash"
  - `isclinical` displays as "iS Clinical"
  - `deese_pro` displays as "Deese PRO"
  - `geske` displays as "Geske"
- Implementation convention (decided in ticket 001 and reused everywhere after): the `store_id` dimension in the dbt model's `_schema.yml` carries `label: Brand` and a value-rename map so the drop down shows the display names instead of the slugs. Do not add a parallel `store_name` column unless ticket 001 specifies otherwise.

### Month filter (dashboard level)
- Label: **"Month"**.
- Values: each calendar month present in the data (auto populated by Lightdash).
- Underlying field: `order_month` on every model with a month of event concept. For sources that don't already have it (Klaviyo, Meta, GA4, Google Ads), the Silver staging model adds `date_trunc('month', <event_timestamp>) as order_month` so a single dashboard filter drives every tile.
- Format: month start date displayed as "April 2026", "March 2026", etc.

### Tile compliance
Every tile produced by these tickets must expose `store_id` and `order_month` (or the equivalent) in its underlying explore. If it does not, the dashboard filters silently won't apply, breaking the API verification step. Confirm this in the Lightdash work section before writing the migration.

## (e) Ticket inventory

Numbering follows reading order through the PDF. The "April value" column is the verification target each ticket must hit when Brand = All, Month = April 2026.

### Cover page (PDF p.1), 4 tickets
| # | Title | PDF April value | Notes |
|---|---|---|---|
| 001 | Combined Shopify Revenue (Apr) | £428,328 (incl HGI) / £425,171 (excl HGI) / £279,895 (today's data) | Also installs dashboard level Brand and Month filters and the `store_id` label/rename convention |
| 002 | Combined Shopify Orders (Apr) | 3,791 (incl HGI) | RL 2,669 + ISC 1,075 + Deese 20 + HGI 27 |
| 003 | Combined Meta Spend (Apr) | £22,581 | 3 accounts: Revitalash, iSC, Deese |
| 004 | Combined Klaviyo Revenue (Apr) | £190,834 | Placed Order, 5 day attribution window |

### Cross brand summary (PDF p.2), 3 tickets
| # | Title | Notes |
|---|---|---|
| 005 | Cross brand "April at a glance" table | Brand, revenue, orders, sessions, trans, CVR, RPS, vs Mar, vs Apr 25 |
| 006 | GA4 revenue share by brand | RL 62.7%, ISC 32.3%, Deese 4.0%, HGI 0.9% (blocked on GA4 for non ISC brands) |
| 007 | Meta spend share by brand | RL £14,467, ISC £7,657, Deese £457, HGI no spend |

### Per brand sections (PDF p.4 to 30), 16 tickets, each brand filterable

PDF page 1 of each brand section: "Revenue & Channel Attribution"
| # | Title | Notes |
|---|---|---|
| 008 | Revenue & Channel Attribution KPI strip | 4 big numbers: total Shopify revenue, GA-attributed revenue, AOV, largest GA channel |
| 009 | Channel breakdown table | Direct, Organic, Paid Search, Paid Social, Email/CRM, Referral, Other by revenue, sessions, trans, vs Mar, vs Apr 25 (needs GA4) |

PDF page 2/3/4/5 of each brand section: "Traffic, conversion, PR, customer mix, AOV"
| # | Title | Notes |
|---|---|---|
| 010 | Traffic & conversion KPI strip | Sessions, users, CVR, RPS, AOV (GA derived). Needs GA4 |
| 011 | Top traffic sources by sessions | Top 8 GA source/medium with sessions, revenue, trans |
| 012 | Top converting sources by RPS | Top 8 GA source/medium with RPS, CVR, trans |
| 013 | PR & media highlights | Top GA4 referrers (sessions, revenue, trans) |
| 014 | Customer mix & AOV split (new vs returning) | Orders, % orders, revenue, % rev, AOV. Shopify source of truth |

PDF page 6 of each brand section: "Paid Media Performance"
| # | Title | Notes |
|---|---|---|
| 015 | Meta ads: remarketing vs acquisition | Audience type, spend, purchases, revenue, ROAS, CPA |
| 016 | Paid search / shopping | Google Ads: branded vs non branded for iSC, channel breakdown for RL/Deese. Partial blocked on Google Ads |

PDF page 7 of each brand section: "CRM Performance"
| # | Title | Notes |
|---|---|---|
| 017 | CRM KPI strip | Total CRM rev, campaign rev, flow rev, active profiles, engaged profiles, open rate, click rate |
| 018 | Top performing campaigns | Klaviyo campaign by revenue (top 5) |
| 019 | Top performing flows | Klaviyo flow by revenue (top 5) |

PDF page 8/9 of each brand section: "12-month subscriber growth"
| # | Title | Notes |
|---|---|---|
| 020 | 12-month subscriber growth totals | Subs added, unsubs, net change |
| 021 | 12-month subscriber growth monthly bar chart | Net subscribers added per month |
| 022 | 12-month subscriber growth monthly table | Month, subscribed, unsubscribed, net |

### Appendix (PDF p.31), 1 ticket
| # | Title | Notes |
|---|---|---|
| 023 | Methodology & data sources sticky note | Markdown tile on the dashboard summarising the source of truth hierarchy from the PDF appendix |

## (f) Generation rules (read this before mass producing tickets)

A future Claude session producing tickets 002 through 023 should follow these rules:

1. **One subagent per ticket.** Spawn a general purpose subagent for each ticket; give it this generator file as context plus the row in section (e). The subagent reads, writes one ticket file, returns. Parallelise within batches of 3 or 4 so context stays bounded.

2. **Verify each PDF reference before writing.** The subagent must open the PDF (Read tool with `pages:`) at the page in the inventory row and confirm the April value before writing it into the ticket. Do not trust the inventory blindly. The PDF wins if they disagree, and the inventory is updated.

3. **Verify the data path before writing the Lightdash work section.** Before writing "tile reads from explore X", `grep` for the relevant Gold model in `dbt/models/gold/` and confirm the columns exist. If the metric requires a model that does not exist, the ticket's "dbt work" section lists creating it. Do not pretend it exists.

4. **Check the data availability map.** If section (c) marks the underlying source as blocked or partial, the ticket's "Data dependencies" section must say so explicitly and link a prerequisite ticket (or describe the prerequisite if no such ticket exists yet).

5. **Mirror the PDF layout decision.** Per brand breakouts that sit visually under their parent KPI on the PDF (e.g. "RL £266k + ISC £144k + ..." under "Combined Shopify Revenue") are bundled into the same ticket. They are one visual unit, they are one ticket.

6. **Push every ticket to Basecamp as HTML.** This is the deliverable: a card in the Triage column whose body renders correctly in Basecamp. The local `tickets/NNN_<slug>.md` file stays in the repo as a reviewable / recoverable copy, but the Basecamp card content must be **HTML, not Markdown**.

   Basecamp's CLI claims to convert Markdown to HTML on the `--content` flag, but empirically it only auto-links URLs. Headings (`#`), bold (`**`), tables, fenced code blocks, blockquotes, ordered lists, all stay as raw characters. So convert with `pandoc` before pushing:

   ```bash
   pandoc -f gfm -t html tickets/NNN_<slug>.md > /tmp/NNN.html
   basecamp card --title "NNN: Title" --content "$(cat /tmp/NNN.html)" --column 9778948514 --in 46863097 --json
   ```

   GFM (`-f gfm`) preserves tables, task lists, fenced code blocks, and strikethrough, all of which the tickets use. Verify the card renders by opening it in Basecamp before moving on (or as part of bulk verification at the end).

7. **Keep the index up to date.** Maintain `tickets/README.md` as the running index (ticket number, title, status, blockers). Add each ticket to it as you write it.

8. **Don't free write.** Use the template in section (b) verbatim. The "Read this first" header, the workflow section, the verification block, all copy paste. Variability lives only in the bracketed placeholders.

9. **No em dashes.** The user's global writing style rule disallows em dashes. Use commas, full stops, colons, or parentheses instead. The card title uses a colon: `001: Combined Shopify Revenue (Apr)`, not `001 — ...`.

10. **Wrap `<placeholder>` text in backticks** (`` `<slug>` `` or fenced code blocks). Even after the pandoc-to-HTML pass, unbacktick'd `<like-this>` text gets eaten by Basecamp's renderer as a stray HTML tag. Backticks make pandoc emit `<code>&lt;like-this&gt;</code>` which renders correctly.

11. **If you update a card (re-push), use `basecamp cards update <id> --content "$(cat /tmp/NNN.html)" --in 46863097 --json`.** Updates are idempotent; safe to re-run after fixing a markdown source.

## (g) Open questions and known gaps to escalate before mass generation

- **iS Clinical Shopify Airbyte sync only has 175 orders since 2026-02-26.** Either the connection is incremental from a recent start date, or there's a stream config issue. Ticket 001 documents this; a separate data engineering ticket needs to fix it before April 2026 verification can pass.
- **Harpar Grace Intl Shopify (harpargrace.com)** is not in the pipeline. The PDF includes 27 HGI orders / £3,157 on the cover. Decide whether to (a) connect harpargrace.com to Airbyte, or (b) accept HGI as an absence from the combined Shopify total.
- **GA4 and Google Ads are only connected for iS Clinical.** A large chunk of the per brand inventory (tickets 009 to 013, 016) cannot verify against non iSC brands' PDF numbers until those connections land. Each affected ticket flags this.
