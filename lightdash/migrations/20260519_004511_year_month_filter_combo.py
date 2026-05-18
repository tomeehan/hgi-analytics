#!/usr/bin/env python3
"""
Replace the KPI Report dashboard's single Month filter with a Year + Month
filter combo. Two short, clean dropdowns instead of one long one.

The previous single-string filter on `fct_orders_order_month_label` was
clunky (Lightdash sorts string filter values alphabetically, so even with
the 'YYYY-MM (Month)' prefix the dropdown still felt unwieldy for picking
arbitrary months). Replacing it with:

  - Year filter  → fct_orders_order_year  (e.g. "2026")
  - Month filter → fct_orders_order_month_name  (e.g. "04 - April")

gives ~5 items in the Year dropdown and 12 in the Month dropdown, both
sorted chronologically.

PR: <to fill in> — feat(lightdash): Year + Month filter combo on KPI Report
Run after: lightdash_deploy.yml succeeds on main (so order_year +
           order_month_name are registered in the Lightdash explore).
Status: pending

This is a ONE-SHOT migration. Idempotent: if the Year/Month filters
already exist, leaves them; if the old `order_month_label` filter is
absent, doesn't remove anything.

Run:
  python3 lightdash/migrations/20260519_004511_year_month_filter_combo.py
  python3 lightdash/migrations/20260519_004511_year_month_filter_combo.py --dry-run
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID  # noqa: E402

KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"

OLD_FIELD_ID = "fct_orders_order_month_label"
YEAR_FIELD_ID = "fct_orders_order_year"
MONTH_FIELD_ID = "fct_orders_order_month_name"

DEFAULT_YEAR = "2026"
DEFAULT_MONTH = "04 - April"


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    dims = dash["filters"]["dimensions"]
    changed = False

    # 1. Drop the old single-string Month filter
    before = len(dims)
    dims[:] = [f for f in dims if f["target"].get("fieldId") != OLD_FIELD_ID]
    if len(dims) != before:
        print(f"  removed old filter on {OLD_FIELD_ID}")
        changed = True

    # 2. Add Year filter if not already present
    if not any(f["target"].get("fieldId") == YEAR_FIELD_ID for f in dims):
        dims.append({
            "id": str(uuid.uuid4()),
            "label": "Year",
            "target": {"fieldId": YEAR_FIELD_ID, "tableName": "fct_orders"},
            "values": [DEFAULT_YEAR],
            "disabled": False,
            "operator": "equals",
            "tileTargets": {},
        })
        print(f"  added Year filter → {YEAR_FIELD_ID} = {DEFAULT_YEAR}")
        changed = True

    # 3. Add Month filter if not already present
    if not any(f["target"].get("fieldId") == MONTH_FIELD_ID for f in dims):
        dims.append({
            "id": str(uuid.uuid4()),
            "label": "Month",
            "target": {"fieldId": MONTH_FIELD_ID, "tableName": "fct_orders"},
            "values": [DEFAULT_MONTH],
            "disabled": False,
            "operator": "equals",
            "tileTargets": {},
        })
        print(f"  added Month filter → {MONTH_FIELD_ID} = {DEFAULT_MONTH}")
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
