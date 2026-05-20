# iS Clinical KPI Report tickets

These tickets rebuild the **iS Clinical version of the April 2026 KPI Report** as the
`kpi-report.yml` Lightdash dashboard, one tile per ticket. They were produced from
`_ticket_generator.md` (the single source of truth for the batch) and each is also a card
in the **Triage** column of the Basecamp Data Engineering board. The reference PDF is
`reference/april_2026_kpi_report.pdf`.

Workflow per ticket: dashboards-as-code (edit `lightdash/charts/` + `lightdash/dashboards/kpi-report.yml`,
preview, PR, auto deploy). See the generator and the CLAUDE.md "Lightdash dashboards-as-code"
section.

Ticket 001 also rescopes the dashboard (renames it, drops the Brand filter, removes the
cross-brand tiles); tickets 002 to 020 each append one tile.

| # | Tile | Status | Notes / blockers |
|---|---|---|---|
| 001 | iS Clinical Shopify Revenue | Triage | Also rescopes the dashboard. Live tile reads ~2.6% low (iSC Shopify sync gap). |
| 002 | iS Clinical Shopify Orders | Triage | iSC Shopify sync gap (1,047 vs 1,075 April orders). |
| 003 | iS Clinical Meta Spend | Triage | Buildable now, no blocker. |
| 004 | iS Clinical Klaviyo Revenue | Triage | Build the Gold revenue model off raw `BRONZE_KLAVIYO_ISCLINICAL.EVENTS` (5-day-window attribution). Data is present, not blocked. |
| 005 | Revenue & Channel Attribution KPI strip | Triage | Shopify numbers carry the iSC sync gap; GA4-attributed figure is fine. |
| 006 | Channel breakdown table | Triage | Needs a new dbt channel-grouping model; per-channel transactions not derivable. |
| 007 | Traffic & conversion KPI strip | Triage | Needs dbt work: users + transactions into `fct_ga_sessions`. |
| 008 | Top traffic sources by sessions | Triage | Needs a new GA4 source/medium dbt model. |
| 009 | Top converting sources by RPS | Triage | Needs the source/medium model; CVR/transactions blocked on a GA4 stream. |
| 010 | PR & media highlights | Triage | Needs the source/medium model; one referrer row does not reconcile. |
| 011 | Customer mix & AOV split | Triage | iSC Shopify sync gap. |
| 012 | Meta ads remarketing vs acquisition | Triage | Needs an audience-type classification in `fct_ad_spend`. |
| 013 | Paid search / shopping | Triage | Google Ads is unmodelled: build the Bronze source + Silver + Gold. |
| 014 | CRM KPI strip | Triage | Revenue + open/click rates buildable off raw `EVENTS`; active/engaged profile counts still need modelling. |
| 015 | Top performing campaigns | Triage | Build campaign revenue off raw `EVENTS` (5-day-window attribution, grouped by campaign). |
| 016 | Top performing flows | Triage | Build flow revenue off raw `EVENTS` (5-day-window attribution); flow names from the `FLOWS` table. |
| 017 | 12-month subscriber growth totals | Triage | Needs a new `fct_klaviyo_subscriber_growth` model (shared with 018, 019). |
| 018 | 12-month subscriber growth monthly bar chart | Triage | Needs `fct_klaviyo_subscriber_growth`. |
| 019 | 12-month subscriber growth monthly table | Triage | Needs `fct_klaviyo_subscriber_growth`. |
| 020 | Methodology & data sources note | Triage | Static markdown tile, no blocker. |
