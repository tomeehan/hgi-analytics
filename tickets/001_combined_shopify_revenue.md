# 001 — Combined Shopify Revenue (April 2026)

> **Read this first if you are a Claude session opening this ticket cold.**
>
> **Project (one paragraph):** This repo is `hgi-analytics`. We ingest Shopify, Klaviyo, Meta, GA4, Google Ads, Cin7 and Prospect CRM into Snowflake via Airbyte, transform with dbt (Bronze → Silver → Gold), and serve dashboards from Lightdash. Full project README is `CLAUDE.md` in the repo root, read it first if you have not seen this project before.
>
> **Wider goal of these tickets:** Recreate the **April 2026 KPI Report** PDF (`reference/april_2026_kpi_report.pdf`) as a live, brand- and month-filterable dashboard in Lightdash. The PDF is treated as numerically authoritative. Each ticket builds one tile on the **Group Overview** dashboard and verifies the April 2026 number against the PDF.
>
> **The generator that produced this ticket:** `tickets/_ticket_generator.md`. Read sections (c) data-availability map and (d) filter design before starting if you have not touched these tickets before.
>
> **Context-window discipline:** Spawn subagents (Explore for codebase searches, Plan for design questions, general-purpose for multi-step research) so this session's context stays focused on the implementation. Do not foreground-read every file linked from this ticket, delegate.

## Basecamp lifecycle (do this, in this order)

1. **Before starting:** find this ticket on the Basecamp Data Engineering card table (account `5735756`, bucket `46863097`, card table `9778948512`) using the `basecamp` skill. Move it from **Triage** to **In progress**.
2. **Do the work** described below.
3. **When the work is done:** add a comment to the Basecamp card with 2 to 4 lines covering (a) the final Lightdash tile location, (b) verification (the SQL snippet from the Verification section, plus the April and March values that should appear), (c) any caveats. Then move the card to **Done**.
4. **Pick up the next ticket:** look at the Basecamp Triage column. If there is another card from this batch (named `NNN — …`), pick the lowest-numbered one and start again from step 1. If Triage is empty for this batch, stop.

## PDF reference
- File: `reference/april_2026_kpi_report.pdf`
- Page 1 (cover), top-left hero KPI, label "COMBINED SHOPIFY REVENUE".
- April 2026 value (PDF): **£428,328**, with footnote breakdown "RL £266,908 + ISC £144,532 + Deese £13,731 + HGI £3,157".
- March 2026 value: not on the PDF cover; capture from Snowflake at verification time and write into the Basecamp comment.

## Metric definition

The total gross Shopify order value for orders created in the selected calendar month, summed across the selected brands. "Gross" here means `total_price` (the Shopify order total before refunds) — the PDF appendix on page 31 names Shopify as the order-count and "true revenue" source of truth without qualifying it further, so we go with the customer-facing order total. If a later ticket needs refunds-adjusted revenue, it should add a separate "Net Shopify Revenue" tile rather than redefining this one.

- Source of truth: Shopify Admin API (via Airbyte → Bronze → `fct_orders`).
- Currency: GBP. All four current Shopify stores settle in GBP, so `total_price` is treated as already-GBP. `CLAUDE.md` flags currency normalisation as undecided — this ticket records the GBP assumption explicitly; revisit if a non-GBP store is added.
- Filter behaviour:
  - **Month filter** changes which month's orders are summed.
  - **Brand filter** = All → sums across every loaded store. Brand = a specific store → shows only that store's revenue (the per-brand breakdown table below makes the other rows show £0, which is the intended behaviour per the layout decision in generator section (d)).

## Data dependencies

### Bronze sources
- ✅ `BRONZE_SHOPIFY_REVITALASH.ORDERS` — 5,578 orders all-time, 2,637 in April 2026 (£263,317).
- ⚠️ `BRONZE_SHOPIFY_DEESE_PRO.ORDERS` — 3,233 orders all-time, 20 in April 2026 (£13,731, matches PDF exactly).
- ❌ `BRONZE_SHOPIFY_ISCLINICAL.ORDERS` — only **175 orders all-time**, earliest 2026-02-26. April 2026 has 29 orders / £3,392 vs the PDF's 1,075 orders / £144,532. This is a **major data gap**, not a metric problem. **This ticket cannot reach the PDF's April number until the iSC Shopify sync is fixed.** Raise a sibling data-engineering ticket: "Backfill/repair iSC Shopify Airbyte sync — only 175 orders since 2026-02-26".
- ❌ `BRONZE_SHOPIFY_GESKE.ORDERS` — Geske bronze schema exists but no `ORDERS` table, so currently contributes £0. Acceptable for April since the PDF doesn't break Geske out separately.
- ❌ `BRONZE_SHOPIFY_HARPER_GRACE` — does not exist; harpargrace.com Shopify is not connected. The £3,157 HGI line on the PDF cover is therefore not reproducible here. Out of scope for this ticket; raise a sibling ticket "Connect harpargrace.com Shopify to Airbyte" if the user wants the HGI line included.

### Silver / Gold models
- ✅ `dbt/models/silver/stg_shopify__orders.sql` — already unions all loaded Shopify stores by `store_id` (per CLAUDE.md "Multi-brand Shopify/Klaviyo union" convention).
- ✅ `dbt/models/gold/fct_orders.sql` — has every column needed: `store_id`, `total_price`, `created_at`, `order_month`, `customer_id`. **No dbt changes are needed.**

### Schema-level work (one-time, lives in this ticket)
- The Brand filter implementation: edit the dbt model's `_schema.yml` (the one that exposes `store_id`) so the dimension has `label: Brand` and a value-rename map: `revitalash → Revitalash`, `isclinical → iS Clinical`, `deese_pro → Deese PRO`, `geske → Geske`. Apply this on whichever `_schema.yml` controls the Lightdash explore for `fct_orders` (search for `fct_orders` in `dbt/models/gold/`). This convention is reused by every subsequent ticket.

## dbt work

- **No new models or columns required.** `fct_orders` already has everything.
- **Schema yml edit:** add `label: Brand` and the value-rename map to the `store_id` dimension on `fct_orders` (per "Schema-level work" above). Run `dbt build --select fct_orders` to confirm the schema change validates.

## Lightdash work

This is the first ticket of the batch, so it also installs the dashboard-level filters that every subsequent ticket depends on.

1. **Add dashboard-level filters to the Group Overview dashboard.**
   - **Brand filter:** label "Brand", target field `fct_orders.store_id` (and via Lightdash's auto-application, every other explore with a `store_id` field), default value **All**.
   - **Month filter:** label "Month", target field `fct_orders.order_month`, default value **April 2026**.
2. **Add a big-number tile** at the top of the Group Overview dashboard, labelled **"Combined Shopify Revenue"**. Underlying explore: `fct_orders`. Metric: `sum(total_price)`. The tile must inherit the Brand + Month dashboard filters (verify by toggling the filter after deploying).
3. **Add a small table tile directly underneath**, labelled **"Per-brand breakdown"**. Underlying explore: `fct_orders`. Dimensions: `store_id` (which now displays as "Brand" with human-readable values). Metric: `sum(total_price)`. Sort by revenue desc.

Migration filename: produced by `bin/new-lightdash-migration combined_shopify_revenue` (yields something like `lightdash/migrations/YYYYMMDD_HHMMSS_combined_shopify_revenue.py`). The migration must:
- Add the two dashboard filters (a one-time setup, idempotent so it can be re-run if Lightdash state drifts).
- Create the two tiles and attach them to dashboard UUID `a8941b36-5393-43fb-9714-cd7edb582803`.
- Support `--dry-run` per the `lightdash/migrations/README.md` pattern.

## Verification

1. Open `https://lightdash.hgi.tomeehan.net/projects/d193767c-d1a9-4861-b591-085254192cce/dashboards/a8941b36-5393-43fb-9714-cd7edb582803`.
2. Set Brand = **All**, Month = **April 2026**.
   - The "Combined Shopify Revenue" tile **today** will show **£279,895** (not the PDF's £428,328 or £425,171). This is expected given the data gaps documented above. Write a Basecamp comment that explains the gap and links the prerequisite tickets (iSC sync, HGI Shopify connect). Once those prerequisites are resolved, re-verify against £425,171 (the PDF total excluding HGI) or £428,328 (incl HGI, after the harpargrace.com store is connected).
   - The "Per-brand breakdown" tile should show:
     - Revitalash £263,317 (PDF: £266,908)
     - iS Clinical £3,392 (PDF: £144,532) — **gap**
     - Deese PRO £13,731 (PDF: £13,731) — matches exactly
     - Geske £0 (PDF: not broken out)
3. Set Month = **March 2026**. Both tiles must change. Capture the values from the live dashboard (and from the SQL below) and write them into the Basecamp comment. If neither tile changes when the month filter changes, the filter is wired incorrectly.
4. Set Brand = **Revitalash**, Month = **April 2026**. The Combined tile should drop to £263,317. The Per-brand table should still show four rows; iS Clinical / Deese / Geske rows are £0. (This is the "filter does not switch the view, only the data" behaviour from generator section (d).)

Reproduce-the-number SQL:
```sql
-- Combined (today's data)
select sum(total_price) as combined_revenue
from HGI.GOLD.FCT_ORDERS
where created_at >= '2026-04-01' and created_at < '2026-05-01';

-- Per-brand breakdown
select store_id, sum(total_price) as revenue, count(*) as orders
from HGI.GOLD.FCT_ORDERS
where created_at >= '2026-04-01' and created_at < '2026-05-01'
group by 1 order by 1;

-- March (for filter-change validation)
select sum(total_price) as combined_revenue
from HGI.GOLD.FCT_ORDERS
where created_at >= '2026-03-01' and created_at < '2026-04-01';
```

## Post-merge ops
This is a Lightdash-touching PR. The PR description must contain:
> Post-deploy ops: wait for `lightdash_deploy.yml` to finish, then run `python3 lightdash/migrations/<the-new-migration>.py`.
(Per `CLAUDE.md` "Lightdash PRs must list post-deploy ops".)

## Update CLAUDE.md if needed
This ticket establishes two new conventions that should be reflected in `CLAUDE.md`:

1. **The dashboard filter convention** (Brand + Month, with the `store_id` label/rename pattern). Add a short note under "Conventions" so the next person touching a Lightdash explore knows to keep the convention.
2. **The store-name display mapping** (`revitalash`/`isclinical`/`deese_pro`/`geske` → human-readable names). Add to the Shopify section under "Conventions".

Update `CLAUDE.md` in the same PR.
