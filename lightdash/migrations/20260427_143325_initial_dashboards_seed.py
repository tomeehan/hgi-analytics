#!/usr/bin/env python3
"""
Initial seed of the HGI Analytics Lightdash dashboards (Group Overview,
Returning Customers, Cross-Brand Customers, UK Regional Performance,
Product Performance, Product Repeat Rate).

PR: #4 (commit f4807ca, 2026-04-27)
Run after: initial Snowflake + Lightdash + dbt setup
Status: applied 2026-04-27

REFERENCE ONLY - DO NOT RE-RUN. This is the one-shot script that
originally created the dashboards listed above. It POSTs new charts
with no upsert, so re-running creates duplicates. Kept in the repo as
a historical record of how the dashboards were initially constructed.

This file has accumulated documentation-style edits in later PRs (#11,
#13, #14, #15) that update the in-source description of each chart's
final state. Those edits were never re-applied — the live dashboards
diverge from this file wherever later migrations made targeted
adjustments. Treat this as the most recent intent of the seed script,
not a faithful snapshot of what was POSTed in April 2026.

For all subsequent chart/dashboard edits, add a new timestamped
migration alongside this one (see ../README.md). Scaffold with
`bin/new-lightdash-migration <slug>`.
"""

import json
import os
import sys
from pathlib import Path

import requests


def _load_env():
    """Populate os.environ from <repo_root>/.env if present (no extra dep)."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


_load_env()

try:
    BASE_URL = os.environ["LIGHTDASH_URL"]
    TOKEN = os.environ["LIGHTDASH_TOKEN"]
    PROJECT_UUID = os.environ["LIGHTDASH_PROJECT_UUID"]
    SPACE_UUID = os.environ["LIGHTDASH_SPACE_UUID"]
except KeyError as e:
    sys.exit(f"Missing required env var {e}. Populate .env (see .env.example).")

HEADERS = {
    "Authorization": f"ApiKey {TOKEN}",
    "Content-Type": "application/json",
}


def api(method, path, body=None):
    url = f"{BASE_URL}/api/v1{path}"
    r = requests.request(method, url, headers=HEADERS, json=body)
    if not r.ok:
        print(f"  ERROR {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    return r.json()["results"]


_TIME_DIMENSION_SUFFIXES = ("_month", "_at", "_date", "_year", "_day", "_week")


def create_chart(name, description, explore, metrics, dimensions,
                 chart_type="cartesian", series_type="bar",
                 sort_field=None, sort_desc=True, limit=20,
                 horizontal=None, filters=None,
                 table_calculations=None, pivot_columns=None,
                 y_field=None):
    """Create a saved chart and return its UUID.

    Bar charts default to horizontal orientation (flipAxes=true). When the
    first dimension looks like a time series (e.g. order_month, ordered_at)
    we keep vertical bars so a chronological axis reads naturally. Pass
    horizontal=True or False to override the auto-detection.
    """
    field_order = dimensions + metrics

    pivot_dimensions = []
    x_field = dimensions[0] if dimensions else None
    y_fields = metrics

    if horizontal is None:
        horizontal = not (x_field and any(x_field.endswith(s) for s in _TIME_DIMENSION_SUFFIXES))

    if chart_type == "cartesian":
        # y_field can be a table-calculation name (raw, no explore prefix) or
        # default to the metric ids derived from `metrics`.
        if y_field is not None:
            y_axis_fields = y_field if isinstance(y_field, list) else [y_field]
        else:
            y_axis_fields = [f"{explore}_{m}" for m in y_fields]
        echarts_config = {
            "series": [
                {
                    "encode": {
                        "xRef": {"field": f"{explore}_{x_field}"},
                        "yRef": {"field": yf},
                    },
                    "type": series_type,
                }
                for yf in y_axis_fields
            ],
        }
        # If the categorical axis is a time dimension, format labels as
        # 'March 2024' so we don't show full ISO timestamps. The time axis
        # is xAxis on vertical charts (default) and yAxis on horizontal.
        # hideOverlap drops labels that don't fit, so dense 24-36 month
        # axes render every Nth label cleanly.
        if x_field and any(x_field.endswith(s) for s in _TIME_DIMENSION_SUFFIXES):
            axis_key = "yAxis" if horizontal else "xAxis"
            echarts_config[axis_key] = [
                {"axisLabel": {"formatter": "{MMMM} {yyyy}", "hideOverlap": True}}
            ]
        chart_config = {
            "type": "cartesian",
            "config": {
                "layout": {
                    "xField": f"{explore}_{x_field}" if x_field else None,
                    "yField": y_axis_fields,
                    "flipAxes": bool(horizontal),
                },
                "eChartsConfig": echarts_config,
            },
        }
    elif chart_type == "pie":
        chart_config = {
            "type": "pie",
            "config": {
                "metricId": f"{explore}_{metrics[0]}",
                "groupFieldIds": [f"{explore}_{dimensions[0]}"],
                "isDonut": False,
            },
        }
    elif chart_type == "big_number":
        chart_config = {
            "type": "big_number",
            "config": {
                "label": name,
                "defaultFormat": None,
                "comparisonFormat": None,
                "flipColors": False,
            },
        }
    elif chart_type == "table":
        chart_config = {
            "type": "table",
            "config": {
                "showColumnCalculation": False,
                "showRowCalculation": False,
                "showTableNames": True,
                "hideRowNumbers": False,
                "metricsAsRows": False,
                "columns": {},
            },
        }
    else:
        chart_config = {"type": chart_type, "config": {}}

    sorts = []
    if sort_field:
        sorts = [{"fieldId": f"{explore}_{sort_field}", "descending": sort_desc}]
    elif metrics:
        sorts = [{"fieldId": f"{explore}_{metrics[0]}", "descending": sort_desc}]

    body = {
        "name": name,
        "description": description,
        "tableName": explore,
        "metricQuery": {
            "exploreName": explore,
            "dimensions": [f"{explore}_{d}" for d in dimensions],
            "metrics": [f"{explore}_{m}" for m in metrics],
            "filters": filters or {},
            "sorts": sorts,
            "limit": limit,
            "tableCalculations": table_calculations or [],
            "additionalMetrics": [],
        },
        "chartConfig": chart_config,
        "tableConfig": {"columnOrder": [f"{explore}_{f}" for f in field_order]},
        "spaceUuid": SPACE_UUID,
    }
    if pivot_columns:
        body["pivotConfig"] = {
            "columns": [f"{explore}_{c}" for c in pivot_columns],
        }

    result = api("POST", f"/projects/{PROJECT_UUID}/saved", body)
    uuid = result["uuid"]
    print(f"  + Chart '{name}' → {uuid}")
    return uuid


def create_dashboard(name, description, chart_uuids):
    """Create a dashboard with chart tiles in a 2-column grid."""
    tiles = []
    for i, uuid in enumerate(chart_uuids):
        col = (i % 2) * 12
        row = (i // 2) * 6
        tiles.append({
            "type": "saved_chart",
            "x": col,
            "y": row,
            "w": 12,
            "h": 6,
            "properties": {"savedChartUuid": uuid, "title": ""},
        })

    body = {
        "name": name,
        "description": description,
        "tiles": tiles,
        "tabs": [],
        "filters": {"dimensions": [], "metrics": [], "tableCalculations": []},
        "spaceUuid": SPACE_UUID,
    }
    result = api("POST", f"/projects/{PROJECT_UUID}/dashboards", body)
    uuid = result["uuid"]
    print(f"\n=> Dashboard '{name}' → {uuid}")
    print(f"   {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{uuid}/view")
    return uuid


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard 1: Group Overview — Revenue & Orders Across All Channels
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/6] Group Overview")

c1 = create_chart(
    "Total Revenue by Month (Cin7)",
    "Monthly revenue across all channels from Cin7 ERP",
    explore="fct_cin7_sales",
    metrics=["total_revenue"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_month",
    sort_desc=False,
    limit=36,
)

c2 = create_chart(
    "Revenue by Channel (Cin7)",
    "Revenue split by sales channel",
    explore="fct_cin7_sales",
    metrics=["total_revenue"],
    dimensions=["channel_group"],
    chart_type="pie",
    limit=10,
)

c3 = create_chart(
    "Direct Shopify Orders by Month",
    "Monthly order count from Shopify Admin API across all 3 active stores "
    "(isClinical, Deese Pro, Revitalash). Volume looks low because most "
    "orders flow through Cin7 — see 'Total Revenue by Month (Cin7)' for "
    "the full B2B + DTC + WooCommerce + Amazon picture.",
    explore="fct_orders",
    metrics=["order_count"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_month",
    sort_desc=False,
    limit=36,
)

c4 = create_chart(
    "Revenue by Store — Shopify",
    "Revenue split by Shopify store",
    explore="fct_orders",
    metrics=["total_revenue"],
    dimensions=["store_id"],
    chart_type="pie",
    limit=10,
)

return_rate_calc = [{
    "name": "return_order_rate",
    "displayName": "Return Order Rate",
    "sql": "1 - (${fct_cin7_sales.new_customer_orders} / NULLIF(${fct_cin7_sales.order_count}, 0))",
    "format": {"type": "percent", "round": 1},
}]

c5 = create_chart(
    "Return Order Rate (Cin7) — All HGI",
    "Percentage of Cin7 orders that are repeat (non-first) orders, across all channels",
    explore="fct_cin7_sales",
    metrics=["order_count", "new_customer_orders"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="line",
    sort_field="order_month",
    sort_desc=False,
    limit=120,
    table_calculations=return_rate_calc,
    y_field="return_order_rate",
)

c6 = create_chart(
    "Average Order Value by Channel (Cin7)",
    "AOV across B2B, DTC, WooCommerce, Amazon",
    explore="fct_cin7_sales",
    metrics=["aov"],
    dimensions=["channel_group"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="aov",
    sort_desc=True,
    limit=10,
)

c5b = create_chart(
    "Return Order Rate (Cin7) — by Channel",
    "Return order rate over time, broken out by Cin7 channel group",
    explore="fct_cin7_sales",
    metrics=["order_count", "new_customer_orders"],
    dimensions=["order_month", "channel_group"],
    chart_type="cartesian",
    series_type="line",
    sort_field="order_month",
    sort_desc=False,
    limit=600,
    table_calculations=return_rate_calc,
    y_field="return_order_rate",
    pivot_columns=["channel_group"],
)

dash1 = create_dashboard(
    "Group Overview — Revenue & Orders",
    "Unified view of revenue and orders across all Cin7 channels and Shopify stores",
    [c1, c2, c3, c4, c5, c6, c5b],
)

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard 2: Returning Customers — This Month vs Last Month
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/6] Returning Customers")

c7 = create_chart(
    "New vs Repeat Orders by Month",
    "Monthly trend of new vs returning customer orders",
    explore="fct_cin7_sales",
    metrics=["order_count", "new_customer_orders"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="line",
    sort_field="order_month",
    sort_desc=False,
    limit=24,
)

c8 = create_chart(
    "Active Customers by Month",
    "Number of unique customers ordering each month",
    explore="fct_cin7_sales",
    metrics=["active_customers"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_month",
    sort_desc=False,
    limit=24,
)

c9 = create_chart(
    "Customer Segments",
    "Breakdown: one-time, occasional (2-4x), loyal (5+) buyers",
    explore="dim_cin7_customers",
    metrics=["customer_count"],
    dimensions=["customer_segment"],
    chart_type="pie",
    limit=10,
)

c10 = create_chart(
    "Revenue by Customer Segment",
    "Total LTV contribution per segment",
    explore="dim_cin7_customers",
    metrics=["total_customer_ltv"],
    dimensions=["customer_segment"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="total_customer_ltv",
    sort_desc=True,
    limit=10,
)

c11 = create_chart(
    "New vs Repeat Orders by Channel",
    "Channel breakdown of new vs returning customers",
    explore="fct_cin7_sales",
    metrics=["order_count", "new_customer_orders"],
    dimensions=["channel_group"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_count",
    sort_desc=True,
    limit=10,
)

c12 = create_chart(
    "Returning Customers — Shopify by Store",
    "New vs returning order count per Shopify store",
    explore="fct_orders",
    metrics=["order_count", "new_customer_orders"],
    dimensions=["store_id"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_count",
    sort_desc=True,
    limit=10,
)

dash2 = create_dashboard(
    "Returning Customers",
    "New vs returning customers this month vs last month, across all channels and stores",
    [c7, c8, c9, c10, c11, c12],
)

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard 3: Cross-Brand Customers
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/6] Cross-Brand Customers")

c13 = create_chart(
    "Customers by Number of Channels Used",
    "How many Cin7 customers have ordered across multiple channels",
    explore="dim_cin7_customers",
    metrics=["customer_count"],
    dimensions=["channels_used"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="channels_used",
    sort_desc=False,
    limit=10,
)

c14 = create_chart(
    "Multi-Channel Customer LTV",
    "Average LTV of customers who shop across channels vs single channel",
    explore="dim_cin7_customers",
    metrics=["avg_ltv", "avg_orders_per_customer"],
    dimensions=["channels_used"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="channels_used",
    sort_desc=False,
    limit=10,
)

c15 = create_chart(
    "Top Customers by Lifetime Value",
    "Highest LTV customers across all channels",
    explore="dim_cin7_customers",
    metrics=["total_customer_ltv", "avg_orders_per_customer"],
    dimensions=["customer_name", "email", "customer_id"],
    chart_type="table",
    sort_field="total_customer_ltv",
    sort_desc=True,
    limit=25,
)

c16 = create_chart(
    "Orders by Month — Shopify DTC",
    "Shopify DTC order trend across both stores",
    explore="fct_orders",
    metrics=["order_count"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="line",
    sort_field="order_month",
    sort_desc=False,
    limit=36,
)

dash3 = create_dashboard(
    "Cross-Brand Customers",
    "Customers shopping across multiple brands and channels — LTV and order frequency",
    [c13, c14, c15, c16],
)

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard 4: UK Regional Performance
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/6] UK Regional Performance")

cin7_uk_only = {
    "dimensions": {
        "id": "cin7-uk-only",
        "and": [{
            "id": "f1",
            "target": {"fieldId": "fct_cin7_sales_uk_region"},
            "operator": "notEquals",
            "values": ["International"],
        }],
    },
}

shopify_uk_only = {
    "dimensions": {
        "id": "shopify-uk-only",
        "and": [{
            "id": "f1",
            "target": {"fieldId": "fct_product_sales_uk_region"},
            "operator": "notEquals",
            "values": ["International"],
        }],
    },
}

c17 = create_chart(
    "Revenue by UK Region (Cin7)",
    "Total revenue per UK region from Cin7 ERP (UK only)",
    explore="fct_cin7_sales",
    metrics=["total_revenue", "order_count"],
    dimensions=["uk_region"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="total_revenue",
    sort_desc=True,
    limit=15,
    filters=cin7_uk_only,
)

c18 = create_chart(
    "AOV by UK Region (Cin7)",
    "Average order value per UK region (UK only)",
    explore="fct_cin7_sales",
    metrics=["aov"],
    dimensions=["uk_region"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="aov",
    sort_desc=True,
    limit=15,
    filters=cin7_uk_only,
)

c19 = create_chart(
    "Revenue by UK Region — Shopify",
    "Total product revenue per UK region from Shopify orders (UK only)",
    explore="fct_product_sales",
    metrics=["product_revenue", "order_count"],
    dimensions=["uk_region"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="product_revenue",
    sort_desc=True,
    limit=15,
    filters=shopify_uk_only,
)

c20 = create_chart(
    "Orders by UK Region — Shopify",
    "Shopify order volume per UK region (UK only)",
    explore="fct_product_sales",
    metrics=["order_count"],
    dimensions=["uk_region"],
    chart_type="pie",
    limit=15,
    filters=shopify_uk_only,
)

dash4 = create_dashboard(
    "UK Regional Performance",
    "Revenue, orders, and AOV broken down by UK region across Cin7 and Shopify",
    [c17, c18, c19, c20],
)

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard 5: Product Performance — Best Sellers & Revenue
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/6] Product Performance")

c21 = create_chart(
    "Top Products by Revenue",
    "Top 20 products by total revenue (GBP)",
    explore="fct_product_sales",
    metrics=["product_revenue"],
    dimensions=["product_title"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="product_revenue",
    sort_desc=True,
    limit=20,
)

c22 = create_chart(
    "Top Products by Units Sold",
    "Top 20 products by quantity sold",
    explore="fct_product_sales",
    metrics=["units_sold"],
    dimensions=["product_title"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="units_sold",
    sort_desc=True,
    limit=20,
)

c23 = create_chart(
    "Top Cross-Sell Pairs",
    "Product pairs most frequently bought together in the same order",
    explore="fct_product_pairs",
    metrics=["times_bought_together"],
    dimensions=["product_a", "product_b"],
    chart_type="table",
    sort_field="times_bought_together",
    sort_desc=True,
    limit=25,
)

c24 = create_chart(
    "Product Revenue by Month",
    "Monthly product revenue trend",
    explore="fct_product_sales",
    metrics=["product_revenue"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_month",
    sort_desc=False,
    limit=24,
)

c25 = create_chart(
    "Revenue by Store — Product View",
    "Product revenue contribution per Shopify store",
    explore="fct_product_sales",
    metrics=["product_revenue"],
    dimensions=["store_id"],
    chart_type="pie",
    limit=10,
)

dash5 = create_dashboard(
    "Product Performance",
    "Best sellers by revenue and units, cross-sell pairs, and revenue trends",
    [c21, c22, c23, c24, c25],
)

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard 6: Product Repeat Rate
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/6] Product Repeat Rate")

c26 = create_chart(
    "Top Products by Repeat Rate",
    "Products with the highest % of buyers who repurchased, split by store",
    explore="fct_product_repeat_rate",
    metrics=["avg_repeat_rate"],
    dimensions=["product_title", "store_id"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="avg_repeat_rate",
    sort_desc=True,
    limit=20,
)

c27 = create_chart(
    "Repeat Buyers vs Unique Buyers",
    "Total buyers vs those who came back, per product per store",
    explore="fct_product_repeat_rate",
    metrics=["total_buyers", "total_repeat_buyers"],
    dimensions=["product_title", "store_id"],
    chart_type="table",
    sort_field="total_buyers",
    sort_desc=True,
    limit=25,
)

c28 = create_chart(
    "Repeat Rate Distribution",
    "Per-product, per-store repeat rate. Same product can show twice "
    "if sold on both isClinical and Deese Pro.",
    explore="fct_product_repeat_rate",
    metrics=["avg_repeat_rate", "total_buyers"],
    dimensions=["product_title", "store_id"],
    chart_type="table",
    sort_field="avg_repeat_rate",
    sort_desc=True,
    limit=50,
)

dash6 = create_dashboard(
    "Product Repeat Rate",
    "Which products bring customers back? Repeat purchase rate per product.",
    [c26, c27, c28],
)

print("\n✓ All 6 dashboards created successfully.")
