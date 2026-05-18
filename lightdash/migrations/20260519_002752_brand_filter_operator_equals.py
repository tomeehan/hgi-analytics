#!/usr/bin/env python3
"""
KPI Report dashboard fixes: (a) Brand filter operator + (b) Month filter
value re-format to match the new sortable label format.

(a) Brand filter was set up with operator `isNotNull` as a "disabled = All
    brands" placeholder. Lightdash's String filter UI has no form for
    `isNotNull` and panics ("No form implemented for String filter
    operator isNotNull") when the chip is clicked. Switch to `equals`
    (disabled, empty values) — semantically equivalent ("no constraint")
    and the form actually renders.

(b) Month filter value was set to "April 2026" by the previous migration
    (to match the `to_char(..., 'MMMM YYYY')` SQL on `order_month_label`).
    The label SQL has now been changed to `'YYYY-MM (Month)'`
    so values look like "2026-04 (April)" — needed because Lightdash
    sorts the dropdown alphabetically and "April 2024 / April 2025 /
    April 2026 / August 2024 ..." is the wrong order for users picking a
    month. Update the saved filter value to match the new format.

PR: <to fill in> — fix(lightdash): KPI Report brand operator + sortable
                   Month filter format
Run after: lightdash_deploy.yml succeeds on main (so `order_month_label`
           reflects the new `'YYYY-MM (Month)'` SQL).
Status: pending

This is a ONE-SHOT migration. Idempotent: only modifies filters that
still hold the old values.

Run:
  python3 lightdash/migrations/20260519_002752_brand_filter_operator_equals.py
  python3 lightdash/migrations/20260519_002752_brand_filter_operator_equals.py --dry-run
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID  # noqa: E402

KPI_REPORT_UUID = "a8941b36-5393-43fb-9714-cd7edb582803"
BRAND_FIELD_ID = "fct_orders_store_id"
MONTH_FIELD_ID = "fct_orders_order_month_label"

# Old format: "April 2026"     | New format: "2026-04 (April)"
MONTH_NAME_YEAR_RE = re.compile(r"^([A-Z][a-z]+)\s+(\d{4})$")
MONTH_NAMES = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def reformat_month_value(value):
    if not isinstance(value, str):
        return value
    m = MONTH_NAME_YEAR_RE.match(value.strip())
    if not m:
        return value  # already new format or unknown — leave alone
    name, year = m.group(1), int(m.group(2))
    if name not in MONTH_NAMES:
        return value
    return f"{year:04d}-{MONTH_NAMES[name]:02d} ({name})"


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    print(f"Dashboard: {KPI_REPORT_UUID} ({'dry-run' if dry_run else 'apply'})")

    dash = api("GET", f"/dashboards/{KPI_REPORT_UUID}")
    changed = False

    for f in dash["filters"]["dimensions"]:
        field_id = f["target"].get("fieldId")

        if field_id == BRAND_FIELD_ID and f.get("operator") == "isNotNull":
            print(f"  brand filter {f['id']}: isNotNull -> equals (disabled, empty values)")
            f["operator"] = "equals"
            f["values"] = []
            f["disabled"] = True
            changed = True

        if field_id == MONTH_FIELD_ID:
            new_values = [reformat_month_value(v) for v in f.get("values", [])]
            if new_values != f.get("values"):
                print(f"  month filter {f['id']}: values {f.get('values')} -> {new_values}")
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
