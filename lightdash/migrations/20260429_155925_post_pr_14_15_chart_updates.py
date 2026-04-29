#!/usr/bin/env python3
"""
Apply the chart-level changes from PRs #14 and #15 to the live Lightdash.

PR: #14 (full-month time labels, currency/percent format) +
    #15 (Top Customers + repeat-rate-by-store + rename Shopify orders)
Run after: lightdash_deploy.yml has finished on main for both PRs.
Status: pending  # flip to "applied YYYY-MM-DD" once it's run cleanly

This is a ONE-SHOT migration. It is idempotent in practice (each step
checks before mutating), but the audit trail is the point — re-running
it later should be unnecessary.

What this does:
  1. DELETE the empty 'Group Command Centre' dashboard.
  2. Swap the eCharts axis-label formatter from {MMM} {yyyy} to
     {MMMM} {yyyy} on every cartesian saved chart in the configured
     space (gives "March 2026" instead of "Mar 2026").
  3. Add `customer_name` + `email` dimensions to "Top Customers by
     Lifetime Value" so the table no longer leads with the GUID.
  4. Add `store_id` to the three repeat-rate charts so per-store
     repeat rate is visible.
  5. Rename "Orders by Month — Shopify" → "Direct Shopify Orders by
     Month" and update the description (the chart already covers all
     3 Shopify stores; volume looks low because Cin7 carries the bulk
     of orders).

Run:
  python3 lightdash/migrations/20260429_155925_post_pr_14_15_chart_updates.py [--dry-run]

The --dry-run flag prints every API call without writing anything.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import api, BASE_URL, PROJECT_UUID, SPACE_UUID  # noqa: E402


DRY_RUN = False


def write(method, path, body=None, *, allow_404=False):
    """Perform a write API call honouring DRY_RUN."""
    if DRY_RUN:
        print(f"    DRY_RUN: would {method} {path}")
        return None
    return api(method, path, body, allow_404=allow_404)


def step_1_delete_empty_dashboard():
    print("\n[1/5] Delete 'Group Command Centre' dashboard (empty)")
    write("DELETE", "/dashboards/1b143813-b21f-48ec-bec6-fb0f222077c9",
          allow_404=True)
    print("    ok")


def step_2_swap_time_formatter():
    print("\n[2/5] Swap {MMM} {yyyy} -> {MMMM} {yyyy} on time-axis charts")
    space = api("GET", f"/projects/{PROJECT_UUID}/spaces/{SPACE_UUID}")
    queries = space.get("queries", [])
    swapped = skipped = 0
    for q in queries:
        chart = api("GET", f"/saved/{q['uuid']}")
        cc = chart.get("chartConfig") or {}
        if cc.get("type") != "cartesian":
            skipped += 1
            continue
        ec = (cc.get("config") or {}).get("eChartsConfig") or {}
        changed = False
        for axis_key in ("xAxis", "yAxis"):
            for ax in (ec.get(axis_key) or []):
                fmt = (ax.get("axisLabel") or {}).get("formatter")
                if fmt == "{MMM} {yyyy}":
                    ax["axisLabel"]["formatter"] = "{MMMM} {yyyy}"
                    changed = True
        if not changed:
            skipped += 1
            continue
        write("POST", f"/saved/{q['uuid']}/version", {
            "metricQuery": chart["metricQuery"],
            "chartConfig": chart["chartConfig"],
            "tableConfig": chart["tableConfig"],
        })
        print(f"    + {chart['name']}")
        swapped += 1
    print(f"    -> {swapped} swapped, {skipped} skipped (already current "
          f"or non-time-series), {len(queries)} total")


def step_3_top_customers_dimensions():
    print("\n[3/5] Top Customers by LTV - add customer_name + email")
    uuid = "aeed7cad-9e40-494c-aa40-dbe3e605ae2f"
    chart = api("GET", f"/saved/{uuid}")
    explore = chart["tableName"]
    new_dims = [
        f"{explore}_customer_name",
        f"{explore}_email",
        f"{explore}_customer_id",
    ]
    if list(chart["metricQuery"]["dimensions"]) == new_dims:
        print("    already current - skipping")
        return
    chart["metricQuery"]["dimensions"] = new_dims
    chart["tableConfig"]["columnOrder"] = (
        new_dims + list(chart["metricQuery"]["metrics"])
    )
    write("POST", f"/saved/{uuid}/version", {
        "metricQuery": chart["metricQuery"],
        "chartConfig": chart["chartConfig"],
        "tableConfig": chart["tableConfig"],
    })
    print("    ok")


def step_4_repeat_rate_store_id():
    print("\n[4/5] Repeat rate charts - add store_id")
    targets = {
        "8b1177a2-8930-4748-a080-98eeff2d876c": "Top Products by Repeat Rate",
        "540c3f8e-dbe6-4136-9b75-918516e4382c": "Repeat Buyers vs Unique Buyers",
        "e528fdfc-3be0-4af1-90f5-5a4ff649fa7b": "Repeat Rate Distribution",
    }
    for uuid, name in targets.items():
        chart = api("GET", f"/saved/{uuid}")
        explore = chart["tableName"]
        store_field = f"{explore}_store_id"
        title_field = f"{explore}_product_title"
        dims = list(chart["metricQuery"]["dimensions"])
        if store_field in dims:
            print(f"    {name}: already has store_id, skipping")
            continue
        idx = dims.index(title_field) + 1 if title_field in dims else len(dims)
        dims.insert(idx, store_field)
        chart["metricQuery"]["dimensions"] = dims
        col_order = list(chart["tableConfig"].get("columnOrder") or [])
        if store_field not in col_order:
            insert_at = (col_order.index(title_field) + 1
                         if title_field in col_order else len(col_order))
            col_order.insert(insert_at, store_field)
        chart["tableConfig"]["columnOrder"] = col_order
        write("POST", f"/saved/{uuid}/version", {
            "metricQuery": chart["metricQuery"],
            "chartConfig": chart["chartConfig"],
            "tableConfig": chart["tableConfig"],
        })
        print(f"    + {name}")


def step_5_rename_shopify_orders():
    print("\n[5/5] Rename 'Orders by Month - Shopify' -> 'Direct Shopify Orders by Month'")
    uuid = "21fbff93-09a8-43c1-a6c7-5a16bab5a465"
    new_name = "Direct Shopify Orders by Month"
    new_desc = (
        "Monthly order count from Shopify Admin API across all 3 active "
        "stores (isClinical, Deese Pro, Revitalash). Volume looks low "
        "because most orders flow through Cin7. See 'Total Revenue by "
        "Month (Cin7)' for the full B2B + DTC + WooCommerce + Amazon "
        "picture."
    )
    chart = api("GET", f"/saved/{uuid}")
    if chart.get("name") == new_name and chart.get("description") == new_desc:
        print("    already current - skipping")
        return
    write("PATCH", f"/saved/{uuid}", {
        "name": new_name,
        "description": new_desc,
    })
    print("    ok")


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print API calls without writing")
    DRY_RUN = parser.parse_args().dry_run

    print(f"Project: {BASE_URL}/projects/{PROJECT_UUID}")
    if DRY_RUN:
        print("DRY RUN - no writes will be performed.")

    step_1_delete_empty_dashboard()
    step_2_swap_time_formatter()
    step_3_top_customers_dimensions()
    step_4_repeat_rate_store_id()
    step_5_rename_shopify_orders()

    print("\nMigration complete.")
    print("  Edit this file's docstring: flip Status to 'applied "
          "YYYY-MM-DD' and commit.")


if __name__ == "__main__":
    main()
