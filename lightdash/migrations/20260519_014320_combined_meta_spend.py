#!/usr/bin/env python3
"""
Add a "Combined Meta Spend" big-number tile to the KPI Report dashboard,
third in the top row of cover KPIs (after Revenue from ticket 001 and
Orders from ticket 002).

Ticket: Data Engineering 003 (Combined Meta Spend (Apr))
PR: <to fill in>
Run after: lightdash_deploy.yml succeeds on main (so the refreshed
           fct_ad_spend explore has store_id Brand label + order_month
           registered).
Status: pending

Idempotent. Re-runs after the chart + tile exist are no-ops.

Run:
  python3 lightdash/migrations/20260519_014320_combined_meta_spend.py --dry-run
  python3 lightdash/migrations/20260519_014320_combined_meta_spend.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402


KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
CHART_NAME = "Combined Meta Spend"
CHART_DESCRIPTION = (
    "Total Meta (Facebook Marketing) ad spend for the month and brands "
    "selected by the dashboard filters. Uses fct_ad_spend.total_meta_spend "
    "(sum of daily spend across iS Clinical, Deese PRO, Revitalash)."
)
EXPLORE = "fct_ad_spend"
METRIC = "fct_ad_spend_total_meta_spend"


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

    # Cover KPIs are big-number tiles on y=0. Revenue is x=0,w=18, Orders is
    # x=18,w=18 (ticket 002 filled the right half). Meta Spend slots onto the
    # next row at x=0,y=4,w=18 — same height. Per-brand breakdown table moves
    # down accordingly (existing tile at y=4 will visually shift to y=8 once
    # this is in; Lightdash auto-flow handles overlap by stacking).
    # Use y=4 for the third KPI; keeps the breakdown table at y=4 visually
    # shifted by Lightdash's grid logic. Actually safer: use the discovered
    # max y so we don't trample the breakdown table.
    max_y = max((t["y"] + t["h"]) for t in dash["tiles"])
    new_tile = {
        "uuid": str(uuid.uuid4()),
        "type": "saved_chart",
        "x": 0,
        "y": max_y,
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
    print(f"  appending tile at x=0, y={max_y} (chart {chart_uuid})")

    if dry_run:
        print("Dry run: skipping PATCH.")
        return

    api("PATCH", f"/dashboards/{KPI_REPORT_UUID}", dash)
    print("Dashboard updated.")


if __name__ == "__main__":
    main()
