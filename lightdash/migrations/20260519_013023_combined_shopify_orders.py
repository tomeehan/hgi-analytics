#!/usr/bin/env python3
"""
Add a "Combined Shopify Orders" big-number tile to the KPI Report dashboard,
mirroring the Combined Shopify Revenue tile installed by ticket 001. Sits
to the right of the Revenue tile on the same row.

Ticket: Data Engineering 002 (Combined Shopify Orders (Apr))
PR: <to fill in>
Run after: lightdash_deploy.yml succeeds on main (no dbt changes here, so
           any recent deploy is fine).
Status: pending

Idempotent: if a saved chart with name "Combined Shopify Orders" already
exists in the target space and the KPI Report already has a tile pointing
at it, the migration is a no-op.

Run:
  python3 lightdash/migrations/20260519_013023_combined_shopify_orders.py --dry-run
  python3 lightdash/migrations/20260519_013023_combined_shopify_orders.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402


KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
CHART_NAME = "Combined Shopify Orders"
CHART_DESCRIPTION = (
    "Count of Shopify orders for the month and brands selected by the "
    "dashboard filters. Uses fct_orders.order_count "
    "(count_distinct on order_id)."
)
EXPLORE = "fct_orders"
METRIC = "fct_orders_order_count"


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
            "dimensions": [],
            "metrics": [METRIC],
            "filters": {},
            "sorts": [],
            "limit": 1,
            "tableCalculations": [],
            "additionalMetrics": [],
            "customDimensions": [],
        },
        "chartConfig": {
            "type": "big_number",
            "config": {
                "label": CHART_NAME,
                "flipColors": False,
                "selectedField": METRIC,
                "showComparison": False,
            },
        },
        "tableConfig": {"columnOrder": []},
    }
    res = api("POST", f"/projects/{PROJECT_UUID}/saved", body)
    return res["uuid"]


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    # 1. Find or create the saved chart
    chart_uuid = find_chart_by_name(CHART_NAME)
    if chart_uuid:
        print(f"  chart '{CHART_NAME}' already exists: {chart_uuid}")
    elif dry_run:
        print(f"  [dry-run] would create chart '{CHART_NAME}' "
              f"on explore={EXPLORE} with metric={METRIC}")
        chart_uuid = "<would-be-created>"
    else:
        chart_uuid = create_chart()
        print(f"  created chart '{CHART_NAME}': {chart_uuid}")

    # 2. Read the dashboard. Skip if a tile already points at this chart.
    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    existing_tile = next(
        (t for t in dash["tiles"]
         if t.get("type") == "saved_chart"
         and t.get("properties", {}).get("savedChartUuid") == chart_uuid),
        None,
    )
    if existing_tile:
        print(f"  tile already on dashboard at "
              f"(x={existing_tile['x']},y={existing_tile['y']}) — done.")
        return

    # 3. Add the tile. The existing Revenue tile is at x=0, y=0, w=18, h=4
    #    on the 36-col grid; place Orders adjacent at x=18, y=0, w=18, h=4
    #    so the layout mirrors the PDF cover (Revenue left, Orders right).
    new_tile = {
        "uuid": str(uuid.uuid4()),
        "type": "saved_chart",
        "x": 18,
        "y": 0,
        "w": 18,
        "h": 4,
        "tabUuid": None,
        "properties": {
            "title": "",
            "hideTitle": False,
            "savedChartUuid": chart_uuid,
            "belongsToDashboard": False,
        },
    }
    dash["tiles"].append(new_tile)
    print(f"  appending tile at x=18, y=0 (chart {chart_uuid})")

    if dry_run:
        print("Dry run: skipping PATCH.")
        return

    api("PATCH", f"/dashboards/{KPI_REPORT_UUID}", dash)
    print("Dashboard updated.")


if __name__ == "__main__":
    main()
