#!/usr/bin/env python3
"""
Build Prospect CRM Lightdash dashboards via REST API.

Prerequisites:
  1. cd dbt && dbt build --select stg_prospect_crm dim_customer_unified fct_b2b_sales
  2. cd dbt && lightdash deploy
  3. .env populated with LIGHTDASH_URL / LIGHTDASH_TOKEN / LIGHTDASH_PROJECT_UUID
     / LIGHTDASH_SPACE_UUID (see .env.example).

Run: python3 lightdash/build_prospect_crm_dashboards.py
"""

import os
import sys
from pathlib import Path

import requests


def _load_env():
    """Populate os.environ from <repo_root>/.env if present (no extra dep)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
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
                 filters=None, horizontal=None):
    """Create a saved chart and return its UUID. Mirrors lightdash/build_dashboards.py.

    Bar charts default to horizontal orientation (flipAxes=true). When the
    first dimension looks like a time series (e.g. order_month, ordered_at)
    we keep vertical bars so a chronological axis reads naturally. Pass
    horizontal=True or False to override the auto-detection.
    """
    field_order = dimensions + metrics
    x_field = dimensions[0] if dimensions else None
    y_fields = metrics

    if horizontal is None:
        horizontal = not (x_field and any(x_field.endswith(s) for s in _TIME_DIMENSION_SUFFIXES))

    if chart_type == "cartesian":
        echarts_config = {
            "series": [
                {
                    "encode": {
                        "xRef": {"field": f"{explore}_{x_field}"},
                        "yRef": {"field": f"{explore}_{m}"},
                    },
                    "type": series_type,
                }
                for m in y_fields
            ],
        }
        # If the categorical axis is a time dimension, format labels as
        # 'Mar 2024' so we don't show full ISO timestamps. The time axis
        # is xAxis on vertical charts (default) and yAxis on horizontal.
        if x_field and any(x_field.endswith(s) for s in _TIME_DIMENSION_SUFFIXES):
            axis_key = "yAxis" if horizontal else "xAxis"
            echarts_config[axis_key] = [
                {"axisLabel": {"formatter": "{MMM} {yyyy}", "hideOverlap": True}}
            ]
        chart_config = {
            "type": "cartesian",
            "config": {
                "layout": {
                    "xField": f"{explore}_{x_field}" if x_field else None,
                    "yField": [f"{explore}_{m}" for m in y_fields],
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
            "tableCalculations": [],
            "additionalMetrics": [],
        },
        "chartConfig": chart_config,
        "tableConfig": {"columnOrder": [f"{explore}_{f}" for f in field_order]},
        "spaceUuid": SPACE_UUID,
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
# Dashboard A: Customer Universe — who is in CRM, who is on Shopify, who is in both
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/3] Customer Universe")

c1 = create_chart(
    "Customers by Universe",
    "Where each customer is seen — CRM only, Shopify only, or both",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["customer_universe"],
    chart_type="pie",
    limit=10,
)

c2 = create_chart(
    "CRM Customers — B2B vs B2C",
    "Distribution of CRM customers across B2B and B2C ledgers",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["seen_in_crm"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="customer_count",
    sort_desc=True,
    limit=5,
)

c3 = create_chart(
    "Customers by Country",
    "Top 15 countries by customer count (CRM-known countries)",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["country"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="customer_count",
    sort_desc=True,
    limit=15,
)

c4 = create_chart(
    "Total DTC Spend by Customer Universe",
    "Lifetime Shopify spend split by where the customer is also seen",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend"],
    dimensions=["customer_universe"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="total_dtc_spend",
    sort_desc=True,
    limit=10,
)

c5 = create_chart(
    "Top DTC Spenders — CRM Presence Flags",
    "Top 50 Shopify spenders, with CRM presence visible",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend", "total_dtc_orders"],
    dimensions=["display_name", "country", "seen_in_crm",
                "customer_universe"],
    chart_type="table",
    sort_field="total_dtc_spend",
    sort_desc=True,
    limit=50,
)

c6 = create_chart(
    "Klaviyo Bridge — Contacts with Klaviyo Profile",
    "CRM contacts that map directly to a Klaviyo profile (~11k expected)",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["seen_in_crm"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="customer_count",
    sort_desc=True,
    limit=5,
    filters={
        "dimensions": {
            "id": "klaviyo-not-null",
            "and": [{
                "id": "f1",
                "target": {"fieldId": "dim_customer_unified_klaviyo_id"},
                "operator": "isNotNull",
            }],
        },
    },
)

dash_a = create_dashboard(
    "Customer Universe — CRM × Shopify",
    "Who are our customers, and which silo(s) do we know them through? "
    "Surfaces the cross-channel overlap (CRM B2B accounts also shopping DTC) "
    "and the single-silo customers each system can't see on its own.",
    [c1, c2, c3, c4, c5, c6],
)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard B: B2B Account 360 — line-level B2B revenue and margin
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/3] B2B Account 360")

c7 = create_chart(
    "B2B Revenue by Month",
    "Monthly B2B sales from Prospect CRM (last 24 months)",
    explore="fct_b2b_sales",
    metrics=["b2b_revenue", "b2b_margin"],
    dimensions=["order_month"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="order_month",
    sort_desc=False,
    limit=24,
)

c8 = create_chart(
    "B2B Revenue by Manufacturer",
    "Which manufacturers drive B2B revenue (top 10)",
    explore="fct_b2b_sales",
    metrics=["b2b_revenue"],
    dimensions=["manufacturer"],
    chart_type="pie",
    limit=10,
)

c9 = create_chart(
    "B2B Margin % by Category",
    "Average margin % per product category (top 15 by line count)",
    explore="fct_b2b_sales",
    metrics=["avg_margin_pct"],
    dimensions=["category_id"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="avg_margin_pct",
    sort_desc=True,
    limit=15,
)

c10 = create_chart(
    "Top B2B Accounts",
    "Top 30 B2B customers by lifetime revenue, with margin and order count",
    explore="fct_b2b_sales",
    metrics=["b2b_revenue", "b2b_margin", "b2b_order_count"],
    dimensions=["customer_name", "country"],
    chart_type="table",
    sort_field="b2b_revenue",
    sort_desc=True,
    limit=30,
)

c11 = create_chart(
    "B2B Revenue by Country",
    "Geographical split of B2B revenue",
    explore="fct_b2b_sales",
    metrics=["b2b_revenue"],
    dimensions=["country"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="b2b_revenue",
    sort_desc=True,
    limit=15,
)

c12 = create_chart(
    "B2B Order Status Mix",
    "Open vs shipped vs invoiced vs other — order status breakdown",
    explore="fct_b2b_sales",
    metrics=["b2b_order_count"],
    dimensions=["order_status"],
    chart_type="pie",
    limit=10,
)

dash_b = create_dashboard(
    "B2B Account 360 — Prospect CRM",
    "Line-level B2B revenue and margin from Prospect CRM. "
    "Filtered to ledgers with is_b2c = false — the ~3,000 wholesale accounts "
    "where Prospect carries the cost data Cin7 doesn't expose at channel grain.",
    [c7, c8, c9, c10, c11, c12],
)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard C: B2B × DTC Cross-View — find B2B accounts also buying DTC
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/3] B2B × DTC Cross-View")

# All charts on this dashboard are filtered to CRM B2B customers,
# revealing which of them also shop DTC on Shopify.
b2b_filter = {
    "dimensions": {
        "id": "b2b-only",
        "and": [{
            "id": "f1",
            "target": {"fieldId": "dim_customer_unified_seen_in_crm"},
            "operator": "equals",
            "values": ["b2b"],
        }],
    },
}

c13 = create_chart(
    "B2B Customers Also Shopping DTC",
    "Of the ~2,500 CRM B2B customers, how many are also Shopify shoppers — split by store",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["customer_universe"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="customer_count",
    sort_desc=True,
    limit=10,
    filters=b2b_filter,
)

c14 = create_chart(
    "DTC Spend by B2B Customers",
    "How much these dual-channel B2B accounts spend on Shopify DTC",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend", "total_dtc_orders"],
    dimensions=["customer_universe"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="total_dtc_spend",
    sort_desc=True,
    limit=10,
    filters=b2b_filter,
)

c15 = create_chart(
    "B2B Accounts with Highest DTC Spend",
    "B2B customers ranked by their personal DTC Shopify spend — "
    "potential signal for cross-channel rep follow-up",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend", "total_dtc_orders"],
    dimensions=["display_name", "country",
                "seen_in_shopify_isclinical", "seen_in_shopify_deese_pro"],
    chart_type="table",
    sort_field="total_dtc_spend",
    sort_desc=True,
    limit=50,
    filters=b2b_filter,
)

c16 = create_chart(
    "B2B Customers by isClinical DTC Spend Tier",
    "Distribution of B2B accounts by their isClinical lifetime spend",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["seen_in_shopify_isclinical"],
    chart_type="pie",
    limit=5,
    filters=b2b_filter,
)

dash_c = create_dashboard(
    "B2B × DTC Cross-View",
    "Cross-channel signal: which B2B (CRM) accounts also shop DTC on Shopify, "
    "and how much they spend there. Useful for rep prioritisation, loyalty "
    "outreach, and identifying wholesale accounts that are testing products via DTC.",
    [c13, c14, c15, c16],
)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard D: DTC → B2B Lead Signals — DTC buyers who look like business
# customers and aren't yet in CRM. Prioritise for B2B outreach.
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/4] DTC → B2B Lead Signals")

lead_filter = {
    "dimensions": {
        "id": "dtc-b2b-leads",
        "and": [{
            "id": "f1",
            "target": {"fieldId": "dim_customer_unified_is_dtc_b2b_lead"},
            "operator": "equals",
            "values": [True],
        }],
    },
}

c17 = create_chart(
    "Likely B2B Leads from DTC",
    "Total customers with business-looking email, real DTC spend, not in CRM",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["is_dtc_b2b_lead"],
    chart_type="big_number",
    limit=2,
    filters=lead_filter,
)

c18 = create_chart(
    "Top Domains by Lead Count",
    "Email domains with the most non-CRM DTC buyers — clinics/businesses sourcing from us",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["email_domain"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="customer_count",
    sort_desc=True,
    limit=20,
    filters=lead_filter,
)

c19 = create_chart(
    "Top Domains by DTC Spend",
    "Email domains contributing most uncaptured B2B revenue (DTC-only spend)",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend"],
    dimensions=["email_domain"],
    chart_type="cartesian",
    series_type="bar",
    sort_field="total_dtc_spend",
    sort_desc=True,
    limit=20,
    filters=lead_filter,
)

c20 = create_chart(
    "Top Individual Leads",
    "Highest-spending DTC-only buyers with business-looking emails — direct outreach list",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend", "total_dtc_orders"],
    dimensions=["display_name", "email", "email_domain", "country",
                "seen_in_shopify_isclinical", "seen_in_shopify_deese_pro"],
    chart_type="table",
    sort_field="total_dtc_spend",
    sort_desc=True,
    limit=50,
    filters=lead_filter,
)

c21 = create_chart(
    "Total Uncaptured DTC Revenue",
    "Sum of DTC spend from likely-B2B leads — the value of converting them to B2B accounts",
    explore="dim_customer_unified",
    metrics=["total_dtc_spend"],
    dimensions=["is_dtc_b2b_lead"],
    chart_type="big_number",
    limit=2,
    filters=lead_filter,
)

c22 = create_chart(
    "Leads by Country",
    "Geographic distribution of likely B2B leads (top 10)",
    explore="dim_customer_unified",
    metrics=["customer_count"],
    dimensions=["country"],
    chart_type="pie",
    limit=10,
    filters=lead_filter,
)

dash_d = create_dashboard(
    "DTC → B2B Lead Signals",
    "DTC Shopify customers who look like business buyers (non-consumer email "
    "domains, real spend) and aren't yet in Prospect CRM. Each row is an "
    "outreach candidate — typically a clinic/business sourcing product via "
    "the consumer storefront. Use 'Top Domains' to spot fleet purchasing.",
    [c17, c18, c19, c20, c21, c22],
)


print("\n" + "=" * 70)
print("Done. Dashboards:")
print(f"  A: {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{dash_a}/view")
print(f"  B: {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{dash_b}/view")
print(f"  C: {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{dash_c}/view")
print(f"  D: {BASE_URL}/projects/{PROJECT_UUID}/dashboards/{dash_d}/view")
