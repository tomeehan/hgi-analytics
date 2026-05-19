#!/usr/bin/env python3
"""
Add the "April at a glance" cross-brand table to the KPI Report dashboard,
mirroring the PDF page 2 showpiece. One row per brand with Shopify
revenue, Shopify orders, GA sessions, GA transactions, Shopify CVR and
Shopify RPS columns.

Ticket: Data Engineering 005 (Cross-brand "April at a glance" table)
PR: <to fill in>
Run after: lightdash_deploy.yml succeeds on main (so
           fct_brand_monthly_summary is registered).
Status: pending

Idempotent: if a saved chart with the same name already exists and the
KPI Report already has a tile pointing at it, the migration is a no-op.

Run:
  python3 lightdash/migrations/20260519_231909_cross_brand_april_at_a_glance.py --dry-run
  python3 lightdash/migrations/20260519_231909_cross_brand_april_at_a_glance.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402


KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
CHART_NAME = "April at a Glance"
CHART_DESCRIPTION = (
    "Cross-brand summary table for the month selected by the dashboard "
    "Month filter. One row per brand, columns mirror the page-2 "
    "'April 2026 at a glance' table of the KPI Report PDF: Revenue "
    "(Shopify), Shopify Orders, Sessions, Trans (GA), Shopify CVR, "
    "Shopify RPS. Reads fct_brand_monthly_summary, which outer-joins "
    "Shopify + GA4 so every loaded brand renders even without GA data. "
    "GA columns populate for iS Clinical only today (other brands' GA4 "
    "Airbyte connections are not yet landed)."
)
EXPLORE = "fct_brand_monthly_summary"
COLUMNS = [
    "fct_brand_monthly_summary_store_id",
    "fct_brand_monthly_summary_shopify_revenue",
    "fct_brand_monthly_summary_shopify_orders",
    "fct_brand_monthly_summary_ga_sessions",
    "fct_brand_monthly_summary_ga_transactions",
    "fct_brand_monthly_summary_shopify_cvr_pct",
    "fct_brand_monthly_summary_shopify_rps_gbp",
]


def find_chart_by_name(name):
    charts = api("GET", f"/projects/{PROJECT_UUID}/charts") or []
    for c in charts:
        if c.get("name") == name:
            return c.get("uuid")
    return None


def create_chart():
    body = {
        "name": CHART_NAME,
        "description": CHART_DESCRIPTION,
        "tableName": EXPLORE,
        "spaceUuid": SPACE_UUID,
        "metricQuery": {
            "exploreName": EXPLORE,
            "dimensions": COLUMNS,
            "metrics": [],
            "filters": {},
            "sorts": [
                {
                    "fieldId": "fct_brand_monthly_summary_shopify_revenue",
                    "descending": True,
                }
            ],
            "limit": 10,
            "tableCalculations": [],
            "additionalMetrics": [],
            "customDimensions": [],
        },
        "chartConfig": {
            "type": "table",
            "config": {
                "showColumnCalculation": False,
                "showRowCalculation": False,
                "showTableNames": True,
                "hideRowNumbers": False,
                "metricsAsRows": False,
            },
        },
        "tableConfig": {"columnOrder": COLUMNS},
    }
    res = api("POST", f"/projects/{PROJECT_UUID}/saved", body)
    return res["uuid"]


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    chart_uuid = find_chart_by_name(CHART_NAME)
    if chart_uuid:
        print(f"  chart '{CHART_NAME}' already exists: {chart_uuid}")
    elif dry_run:
        print(f"  [dry-run] would create chart '{CHART_NAME}' "
              f"on explore={EXPLORE}")
        chart_uuid = "<would-be-created>"
    else:
        chart_uuid = create_chart()
        print(f"  created chart '{CHART_NAME}': {chart_uuid}")

    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    existing_tile = next(
        (t for t in dash["tiles"]
         if t.get("type") == "saved_chart"
         and t.get("properties", {}).get("savedChartUuid") == chart_uuid),
        None,
    )
    if existing_tile:
        print(f"  tile already on dashboard at "
              f"(x={existing_tile['x']},y={existing_tile['y']}). Done.")
        return

    # Full-width table tile under the cover KPIs. Lightdash auto-reflows
    # so we just append at the next free row.
    max_y = max((t["y"] + t["h"]) for t in dash["tiles"])
    new_tile = {
        "uuid": str(uuid.uuid4()),
        "type": "saved_chart",
        "x": 0,
        "y": max_y,
        "w": 36,
        "h": 6,
        "tabUuid": None,
        "properties": {
            "title": "",
            "hideTitle": False,
            "savedChartUuid": chart_uuid,
            "belongsToDashboard": False,
        },
    }
    dash["tiles"].append(new_tile)
    print(f"  appending full-width tile at x=0, y={max_y} (chart {chart_uuid})")

    if dry_run:
        print("Dry run: skipping PATCH.")
        return

    api("PATCH", f"/dashboards/{KPI_REPORT_UUID}", dash)
    print("Dashboard updated.")


if __name__ == "__main__":
    main()
