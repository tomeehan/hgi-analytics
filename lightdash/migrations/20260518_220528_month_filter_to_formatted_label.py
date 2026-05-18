#!/usr/bin/env python3
"""
Retarget the KPI Report dashboard's Month filter to the new `order_month_label`
dimension so the filter chip/dropdown reads "April 2026" instead of the raw
ISO timestamp "2026-04-01T00:00:00.000Z".

PR: <to fill in> — chore(lightdash): readable Month filter on KPI Report
Run after: lightdash_deploy.yml succeeds on main (so `order_month_label`
           is registered in the Lightdash explore for fct_orders).
Status: pending  # flip to "applied YYYY-MM-DD" once it's run cleanly

This is a ONE-SHOT migration. Re-running is harmless (idempotent — it only
PATCHes filters that still reference the old `fct_orders_order_month`
fieldId with an ISO date value).

What this does:
  - Walks the KPI Report dashboard (only dashboard with a Month filter today)
  - For each dimension filter where target.fieldId == "fct_orders_order_month"
    AND values look like an ISO date string ("YYYY-MM-DD..."), retargets to
    "fct_orders_order_month_label" and reformats values as "Month YYYY".

Run:
  python3 lightdash/migrations/20260518_220528_month_filter_to_formatted_label.py
  python3 lightdash/migrations/20260518_220528_month_filter_to_formatted_label.py --dry-run
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID  # noqa: E402


KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
OLD_FIELD_ID = "fct_orders_order_month"
NEW_FIELD_ID = "fct_orders_order_month_label"
ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-\d{2}")


def to_label(value: str) -> str:
    """'2026-04-01' or '2026-04-01T00:00:00.000Z' -> 'April 2026'."""
    m = ISO_DATE_RE.match(value)
    if not m:
        return value  # already a label, leave alone
    return datetime(int(m.group(1)), int(m.group(2)), 1).strftime("%B %Y")


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    dims = dash["filters"]["dimensions"]
    changed = False
    for f in dims:
        if f["target"].get("fieldId") != OLD_FIELD_ID:
            continue
        new_values = [to_label(v) if isinstance(v, str) else v for v in f.get("values", [])]
        if new_values == f.get("values") and f["target"].get("fieldId") == NEW_FIELD_ID:
            print(f"  filter {f['id']}: already on new fieldId — skipping")
            continue
        print(f"  filter {f['id']}: {OLD_FIELD_ID} -> {NEW_FIELD_ID}; values {f.get('values')} -> {new_values}")
        f["target"]["fieldId"] = NEW_FIELD_ID
        f["values"] = new_values
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
