#!/usr/bin/env python3
"""
Switch the KPI Report's Month filter to target the new YYYY-MM string
label dimension (`fct_orders_order_month_label`) so the dropdown is a
proper string dropdown sorted chronologically (`2025-12`, `2026-01`,
`2026-02`, ...). The previous attempt to use the DATE column directly
with `format: 'mmmm yyyy'` failed — Lightdash gave a date-picker UI and
ignored the format on the filter chip.

PR: #40 — feat(lightdash): single Month filter as YYYY-MM string
Run after: lightdash_deploy.yml succeeds on main (so `order_month_label`
           is registered in the Lightdash explore).
Status: applied 2026-05-19

Idempotent: only patches if the filter still targets `fct_orders_order_month`.

Run:
  python3 lightdash/migrations/20260519_012321_month_filter_yyyymm_label.py
  python3 lightdash/migrations/20260519_012321_month_filter_yyyymm_label.py --dry-run
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID  # noqa: E402

KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
OLD_FIELD_ID = "fct_orders_order_month"
NEW_FIELD_ID = "fct_orders_order_month_label"
DEFAULT_VALUE = "2026-04"  # April 2026


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    dims = dash["filters"]["dimensions"]
    changed = False

    # 1. Drop any existing filter on the old DATE column
    before = len(dims)
    dims[:] = [f for f in dims if f["target"].get("fieldId") != OLD_FIELD_ID]
    if len(dims) != before:
        print(f"  removed old filter on {OLD_FIELD_ID}")
        changed = True

    # 2. Add new filter on the YYYY-MM label dim (idempotent)
    if not any(f["target"].get("fieldId") == NEW_FIELD_ID for f in dims):
        dims.append({
            "id": str(uuid.uuid4()),
            "label": "Month",
            "target": {"fieldId": NEW_FIELD_ID, "tableName": "fct_orders"},
            "values": [DEFAULT_VALUE],
            "disabled": False,
            "operator": "equals",
            "tileTargets": {},
        })
        print(f"  added Month filter → {NEW_FIELD_ID} = {DEFAULT_VALUE}")
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
