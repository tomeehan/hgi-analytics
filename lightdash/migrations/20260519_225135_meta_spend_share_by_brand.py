#!/usr/bin/env python3
"""
Add a "Meta Spend Share by Brand" horizontal bar tile to the KPI Report
dashboard, mirroring the page-2 "META SPEND SHARE BY BRAND" sub-box of
the April 2026 KPI Report PDF.

Ticket: Data Engineering 007 (Meta spend share by brand)
PR: <to fill in>
Run after: lightdash_deploy.yml succeeds on main.
Status: pending

Idempotent: if a saved chart with name "Meta Spend Share by Brand" already
exists in the target space and the KPI Report already has a tile pointing
at it, the migration is a no-op.

Run:
  python3 lightdash/migrations/20260519_225135_meta_spend_share_by_brand.py --dry-run
  python3 lightdash/migrations/20260519_225135_meta_spend_share_by_brand.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402


KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
CHART_NAME = "Meta Spend Share by Brand"
CHART_DESCRIPTION = (
    "Total Meta ad spend per brand for the month selected by the dashboard "
    "Month filter. Horizontal bar chart with one bar per brand. Mirrors the "
    "page-2 'META SPEND SHARE BY BRAND' sub-box of the April 2026 KPI "
    "Report PDF (RL £14,467, ISC £7,657, Deese £457, HGI no spend). "
    "Today's Bronze data is dramatically short on RL spend (~£423 vs PDF "
    "£14,467), so the live chart will not match the PDF magnitudes until "
    "the Meta Revitalash sync catches up."
)
EXPLORE = "fct_ad_spend"
DIMENSION = "fct_ad_spend_store_id"
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
            "dimensions": [DIMENSION],
            "metrics": [METRIC],
            "filters": {},
            "sorts": [{"fieldId": METRIC, "descending": True}],
            "limit": 10,
            "tableCalculations": [],
            "additionalMetrics": [],
            "customDimensions": [],
        },
        "chartConfig": {
            "type": "cartesian",
            "config": {
                "layout": {
                    "xField": DIMENSION,
                    "yField": [METRIC],
                    "flipAxes": True,
                },
                "eChartsConfig": {
                    "series": [
                        {
                            "encode": {
                                "xRef": {"field": DIMENSION},
                                "yRef": {"field": METRIC},
                            },
                            "type": "bar",
                        }
                    ],
                },
            },
        },
        "tableConfig": {"columnOrder": [DIMENSION, METRIC]},
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
              f"on explore={EXPLORE} (dim={DIMENSION}, metric={METRIC})")
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

    # Append below current tiles, matching the cross-brand summary section of
    # the PDF (page 2 right-hand sub-box). Lightdash's grid auto-reflows on
    # save so we don't have to compute exact x/y; we just take the next free y.
    max_y = max((t["y"] + t["h"]) for t in dash["tiles"])
    new_tile = {
        "uuid": str(uuid.uuid4()),
        "type": "saved_chart",
        "x": 18,
        "y": max_y,
        "w": 18,
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
    print(f"  appending tile at x=18, y={max_y} (chart {chart_uuid})")

    if dry_run:
        print("Dry run: skipping PATCH.")
        return

    api("PATCH", f"/dashboards/{KPI_REPORT_UUID}", dash)
    print("Dashboard updated.")


if __name__ == "__main__":
    main()
