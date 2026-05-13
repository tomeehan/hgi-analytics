#!/usr/bin/env python3
"""
Seed the KPI Report dashboard with Brand+Month filters and the Combined
Shopify Revenue tile + per-brand breakdown.

PR: TBD (Ticket 001 - Combined Shopify Revenue)
Run after: lightdash_deploy.yml succeeds on main (so the Brand label /
value remap on fct_orders.store_id is picked up by Lightdash).
Status: applied 2026-05-13

This is a ONE-SHOT migration. Re-running will create duplicate saved
charts and reset the dashboard tile layout.

What this does:
  - Creates two saved charts on the fct_orders explore:
      * Big-number "Combined Shopify Revenue"  (sum of total_price)
      * Table "Per-brand breakdown"            (sum of total_price grouped by store_id)
  - PATCHes dashboard a8941b36-5393-43fb-9714-cd7edb582803 ("KPI Report"):
      * Adds two dashboard-level filters: Brand (default: All) and
        Month (default: April 2026). The Brand filter is created
        disabled to act as "All"; users can toggle it to filter.
      * Replaces the dashboard's tile list with the two new tiles.

Run:
  python3 lightdash/migrations/20260513_164850_combined_shopify_revenue.py [--dry-run]
"""

import json
import sys
import uuid as _uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402

DRY_RUN = "--dry-run" in sys.argv

DASHBOARD_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
EXPLORE = "fct_orders"

STORE_ID_FIELD = f"{EXPLORE}_store_id"
ORDER_MONTH_FIELD = f"{EXPLORE}_order_month"
TOTAL_REVENUE_METRIC = f"{EXPLORE}_total_revenue"

DEFAULT_MONTH = "2026-04-01"  # April 2026


def write(method, path, body=None, *, allow_404=False):
    """Wrap api() to honour --dry-run."""
    if DRY_RUN and method != "GET":
        body_preview = json.dumps(body)[:140] if body else ""
        print(f"  [dry-run] {method} {path}  {body_preview}")
        # Fake a sensible return so downstream code keeps flowing.
        return {"uuid": f"dry-run-{path.rsplit('/', 1)[-1]}"}
    return api(method, path, body=body, allow_404=allow_404)


def create_combined_revenue_chart():
    """Big-number tile: sum of total_price."""
    body = {
        "name": "Combined Shopify Revenue",
        "description": (
            "Sum of Shopify gross order value (total_price) for the "
            "month and brands selected by the dashboard filters."
        ),
        "tableName": EXPLORE,
        "metricQuery": {
            "exploreName": EXPLORE,
            "dimensions": [],
            "metrics": [TOTAL_REVENUE_METRIC],
            "filters": {},
            "sorts": [],
            "limit": 1,
            "tableCalculations": [],
            "additionalMetrics": [],
        },
        "chartConfig": {
            "type": "big_number",
            "config": {
                "label": "Combined Shopify Revenue",
                "selectedField": TOTAL_REVENUE_METRIC,
                "showComparison": False,
                "flipColors": False,
            },
        },
        "tableConfig": {"columnOrder": [TOTAL_REVENUE_METRIC]},
        "spaceUuid": SPACE_UUID,
    }
    result = write("POST", f"/projects/{PROJECT_UUID}/saved", body)
    uuid = result["uuid"]
    print(f"  + Chart 'Combined Shopify Revenue' -> {uuid}")
    return uuid


def create_breakdown_chart():
    """Table tile: revenue by brand, descending."""
    body = {
        "name": "Per-brand breakdown",
        "description": (
            "Shopify gross revenue (sum of total_price) grouped by brand. "
            "Inherits the dashboard's Brand + Month filters."
        ),
        "tableName": EXPLORE,
        "metricQuery": {
            "exploreName": EXPLORE,
            "dimensions": [STORE_ID_FIELD],
            "metrics": [TOTAL_REVENUE_METRIC],
            "filters": {},
            "sorts": [{"fieldId": TOTAL_REVENUE_METRIC, "descending": True}],
            "limit": 500,
            "tableCalculations": [],
            "additionalMetrics": [],
        },
        "chartConfig": {
            "type": "table",
            "config": {
                "showColumnCalculation": False,
                "showRowCalculation": False,
                "showTableNames": False,
                "showResultsTotal": False,
                "hideRowNumbers": True,
                "metricsAsRows": False,
                "columns": {},
                "conditionalFormattings": [],
            },
        },
        "tableConfig": {
            "columnOrder": [STORE_ID_FIELD, TOTAL_REVENUE_METRIC],
        },
        "spaceUuid": SPACE_UUID,
    }
    result = write("POST", f"/projects/{PROJECT_UUID}/saved", body)
    uuid = result["uuid"]
    print(f"  + Chart 'Per-brand breakdown' -> {uuid}")
    return uuid


def patch_dashboard(combined_uuid, breakdown_uuid):
    """Set the KPI Report dashboard's filters and tiles in one PATCH."""
    brand_filter = {
        "id": str(_uuid.uuid4()),
        "label": "Brand",
        "target": {"fieldId": STORE_ID_FIELD, "tableName": EXPLORE},
        "operator": "isNotNull",
        "values": [],
        "disabled": True,  # "All" by default; user enables to filter to a single brand
        "tileTargets": {},
    }
    month_filter = {
        "id": str(_uuid.uuid4()),
        "label": "Month",
        "target": {"fieldId": ORDER_MONTH_FIELD, "tableName": EXPLORE},
        "operator": "equals",
        "values": [DEFAULT_MONTH],
        "disabled": False,
        "tileTargets": {},
    }

    tiles = [
        {
            "type": "saved_chart",
            "x": 0,
            "y": 0,
            "w": 18,
            "h": 4,
            "tabUuid": None,
            "properties": {
                "title": "",
                "hideTitle": False,
                "savedChartUuid": combined_uuid,
                "belongsToDashboard": False,
            },
        },
        {
            "type": "saved_chart",
            "x": 0,
            "y": 4,
            "w": 18,
            "h": 5,
            "tabUuid": None,
            "properties": {
                "title": "",
                "hideTitle": False,
                "savedChartUuid": breakdown_uuid,
                "belongsToDashboard": False,
            },
        },
    ]

    body = {
        "name": "KPI Report",
        "tiles": tiles,
        "tabs": [],
        "filters": {
            "dimensions": [brand_filter, month_filter],
            "metrics": [],
            "tableCalculations": [],
        },
    }
    write("PATCH", f"/dashboards/{DASHBOARD_UUID}", body)
    print(f"\n=> Dashboard 'KPI Report' updated")
    print(f"   {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{DASHBOARD_UUID}/view")


def main():
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Mode:    {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print()

    combined_uuid = create_combined_revenue_chart()
    breakdown_uuid = create_breakdown_chart()
    patch_dashboard(combined_uuid, breakdown_uuid)


if __name__ == "__main__":
    main()
