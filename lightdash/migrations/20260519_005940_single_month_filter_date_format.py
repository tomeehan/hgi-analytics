#!/usr/bin/env python3
"""
Replace the Year + Month filter combo with a single Month filter targeting
the DATE-typed `fct_orders.order_month`. The dbt schema now has
`format: 'mmmm yyyy'` on that column, which tells Lightdash to render
values as "April 2026" via numfmt while keeping the underlying type DATE
— so the filter dropdown sorts chronologically out of the box and shows
one clean dropdown of human-readable labels.

PR: #38 — feat(lightdash): single Month filter, chronological,
          rendered as "April 2026"
Run after: lightdash_deploy.yml succeeds on main (so `order_month`
           inherits the new `format` and the now-unused `order_year` /
           `order_month_name` additional dimensions are gone).
Status: applied 2026-05-19

This is a ONE-SHOT migration. Idempotent: only patches the KPI Report
dashboard's filters, and only if the Year/Month combo is still present.

Run:
  python3 lightdash/migrations/20260519_005940_single_month_filter_date_format.py
  python3 lightdash/migrations/20260519_005940_single_month_filter_date_format.py --dry-run
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID  # noqa: E402

KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"

OLD_FIELD_IDS = {"fct_orders_order_year", "fct_orders_order_month_name"}
NEW_FIELD_ID = "fct_orders_order_month"
DEFAULT_DATE_VALUE = "2026-04-01"  # April 2026


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    dims = dash["filters"]["dimensions"]
    changed = False

    # 1. Drop Year + Month combo
    before = len(dims)
    dims[:] = [f for f in dims if f["target"].get("fieldId") not in OLD_FIELD_IDS]
    removed = before - len(dims)
    if removed:
        print(f"  removed {removed} filter(s) on Year/Month combo")
        changed = True

    # 2. Add single Month filter on order_month (DATE), unless already present
    if not any(f["target"].get("fieldId") == NEW_FIELD_ID for f in dims):
        dims.append({
            "id": str(uuid.uuid4()),
            "label": "Month",
            "target": {"fieldId": NEW_FIELD_ID, "tableName": "fct_orders"},
            "values": [DEFAULT_DATE_VALUE],
            "disabled": False,
            "operator": "equals",
            "tileTargets": {},
        })
        print(f"  added Month filter → {NEW_FIELD_ID} = {DEFAULT_DATE_VALUE}")
        changed = True

    if not changed:
        print("Nothing to update.")
        return

    if dry_run:
        print("Dry run: skipping PATCH.")
        return

    api("PATCH", f"/dashboards/{KPI_REPORT_UUID}", dash)
    print("Dashboard updated.")


if __name__ == "__main__":
    main()
