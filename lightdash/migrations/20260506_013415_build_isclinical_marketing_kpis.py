#!/usr/bin/env python3
"""
Build the "isClincal Marketing KPIs" dashboard with 10 Big Number tiles.

PR: feat/isclinical-marketing-kpis
Run after: lightdash_deploy.yml succeeds on main (so the new explore
fct_marketing_kpis_daily is discoverable in Lightdash)
Status: pending  # flip to "applied YYYY-MM-DD" once it's run cleanly

This is a ONE-SHOT migration. Re-running may create duplicate charts /
dashboards or fail.

What this does:
  - Creates 10 Big Number saved charts on the fct_marketing_kpis_daily
    explore. Each chart selects two metrics (L30D + Prev 30D) and uses
    Lightdash's Big Number `selectedField` + `comparisonField` to render
    "headline number + comparison" sub-text vs the previous 30 days.
  - Creates one dashboard, "isClincal Marketing KPIs", with the 10 charts
    laid out in a 4-column grid (3 rows: 4+4+2).
  - After creating the first chart, GETs it back and asserts that
    `comparisonField` round-tripped through the API. If not, stops the
    script before creating the other 9.

Run:
  python3 lightdash/migrations/20260506_013415_build_isclinical_marketing_kpis.py [--dry-run]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402

DRY_RUN = "--dry-run" in sys.argv

EXPLORE = "fct_marketing_kpis_daily"

# (chart_name, l30d_metric, p30d_metric)
TILES = [
    ("Gross Sales",                "gross_sales_l30d",        "gross_sales_p30d"),
    ("Net Sales",                  "net_sales_l30d",          "net_sales_p30d"),
    ("Total Orders",               "orders_l30d",             "orders_p30d"),
    ("Average Order Value",        "aov_l30d",                "aov_p30d"),
    ("Ad Spend",                   "ad_spend_l30d",           "ad_spend_p30d"),
    ("Blended ROAS (MER)",         "blended_roas_l30d",       "blended_roas_p30d"),
    ("New Customer %",             "new_customer_pct_l30d",   "new_customer_pct_p30d"),
    ("Blended CAC",                "blended_cac_l30d",        "blended_cac_p30d"),
    ("Sessions",                   "sessions_l30d",           "sessions_p30d"),
    ("Shopify Conversion Rate",    "conversion_rate_l30d",    "conversion_rate_p30d"),
]

# Brand filter — applied to every chart. Period windows are baked into the
# metric SQL via `case when date >= current_date - 30`, so no date filter is
# needed on the chart itself.
ISCLINICAL_FILTER = {
    "dimensions": {
        "id": "isclinical-only",
        "and": [{
            "id": "f1",
            "target": {"fieldId": f"{EXPLORE}_store_id"},
            "operator": "equals",
            "values": ["isclinical"],
        }],
    },
}


def write(method, path, body=None, *, allow_404=False):
    """Wrap api() to honour --dry-run."""
    if DRY_RUN and method != "GET":
        body_preview = ""
        if body:
            import json
            body_preview = json.dumps(body)[:120]
        print(f"  [dry-run] {method} {path}  {body_preview}")
        return {"uuid": f"dry-run-{path.rsplit('/', 1)[-1]}"}
    return api(method, path, body=body, allow_404=allow_404)


def build_chart(name, l30d, p30d):
    """POST a Big Number saved chart and return its UUID."""
    l30d_field = f"{EXPLORE}_{l30d}"
    p30d_field = f"{EXPLORE}_{p30d}"

    body = {
        "name": name,
        "description": (
            f"isClinical, last 30 days vs previous 30 days. "
            f"Headline = {l30d}; comparison = {p30d}."
        ),
        "tableName": EXPLORE,
        "metricQuery": {
            "exploreName": EXPLORE,
            "dimensions": [],
            "metrics": [l30d_field, p30d_field],
            "filters": ISCLINICAL_FILTER,
            "sorts": [],
            "limit": 1,
            "tableCalculations": [],
            "additionalMetrics": [],
        },
        "chartConfig": {
            "type": "big_number",
            "config": {
                "label": name,
                "selectedField": l30d_field,
                "comparisonField": p30d_field,
                "showComparison": True,
                "comparisonFormat": "percentage",
                "flipColors": False,
                "comparisonLabel": "vs previous 30 days",
            },
        },
        "tableConfig": {"columnOrder": [l30d_field, p30d_field]},
        "spaceUuid": SPACE_UUID,
    }
    result = write("POST", f"/projects/{PROJECT_UUID}/saved", body)
    uuid = result["uuid"]
    print(f"  + Chart '{name}' -> {uuid}")
    return uuid


def assert_comparison_roundtrips(chart_uuid, expected_l30d, expected_p30d):
    """Fetch the chart back and assert the Big Number comparison config survived."""
    if DRY_RUN:
        print("  [dry-run] skipping comparison-field round-trip check")
        return
    chart = api("GET", f"/saved/{chart_uuid}")
    cfg = chart.get("chartConfig", {}).get("config", {}) or {}
    expected_l30d_field = f"{EXPLORE}_{expected_l30d}"
    expected_p30d_field = f"{EXPLORE}_{expected_p30d}"
    problems = []
    if cfg.get("selectedField") != expected_l30d_field:
        problems.append(
            f"selectedField got {cfg.get('selectedField')!r}, expected {expected_l30d_field!r}"
        )
    if cfg.get("comparisonField") != expected_p30d_field:
        problems.append(
            f"comparisonField got {cfg.get('comparisonField')!r}, expected {expected_p30d_field!r}"
        )
    if cfg.get("showComparison") is not True:
        problems.append(f"showComparison got {cfg.get('showComparison')!r}, expected True")
    if problems:
        print()
        print("  Big Number comparison config did NOT round-trip through the API:")
        for p in problems:
            print(f"      - {p}")
        print()
        print("  STOPPING. The first chart was created but is not configured as expected.")
        print("  Investigate before re-running. Do not let the script create the other 9.")
        sys.exit(1)
    print("  Big Number comparison config round-trips correctly.")


def build_dashboard(chart_uuids):
    """4-column grid: w=6, h=3 each. 10 tiles -> 3 rows (4+4+2)."""
    tiles = []
    for i, uuid in enumerate(chart_uuids):
        col = (i % 4) * 6
        row = (i // 4) * 3
        tiles.append({
            "type": "saved_chart",
            "x": col,
            "y": row,
            "w": 6,
            "h": 3,
            "properties": {"savedChartUuid": uuid, "title": ""},
        })

    body = {
        "name": "isClincal Marketing KPIs",
        "description": (
            "isClinical marketing KPIs. Last 30 days vs previous 30 days. "
            "Ad spend is Meta only (Google Ads pending source-side fix)."
        ),
        "tiles": tiles,
        "tabs": [],
        "filters": {"dimensions": [], "metrics": [], "tableCalculations": []},
        "spaceUuid": SPACE_UUID,
    }
    result = write("POST", f"/projects/{PROJECT_UUID}/dashboards", body)
    uuid = result["uuid"]
    print(f"\n=> Dashboard 'isClincal Marketing KPIs' -> {uuid}")
    print(f"   {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{uuid}/view")
    return uuid


def main():
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Mode:    {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print()

    chart_uuids = []
    for i, (name, l30d, p30d) in enumerate(TILES):
        uuid = build_chart(name, l30d, p30d)
        chart_uuids.append(uuid)
        if i == 0:
            assert_comparison_roundtrips(uuid, l30d, p30d)

    build_dashboard(chart_uuids)


if __name__ == "__main__":
    main()
