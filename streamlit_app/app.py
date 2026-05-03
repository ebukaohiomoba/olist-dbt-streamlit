"""Olist Executive Overview — Streamlit dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import load_table

st.set_page_config(
    page_title="Olist Executive Overview",
    page_icon="📦",
    layout="wide",
)

st.title("Olist Executive Overview")
st.caption("2016–2018 Brazilian e-commerce — orders, revenue, delivery, geography")


# ---------- data loaders (pandas-side aggregation so they work in both Postgres and parquet modes) ----------

@st.cache_data(ttl=600, show_spinner="Loading order metrics...")
def load_kpis() -> dict:
    orders = load_table("fct_orders")
    delivered = orders[orders["order_status"] == "delivered"]
    return {
        "total_orders":          len(delivered),
        "total_customers":       delivered["customer_id"].nunique(),
        "total_revenue":         delivered["payment_total"].sum(),
        "avg_order_value":       delivered["payment_total"].mean(),
        "on_time_rate":          delivered["delivered_on_time"].astype(float).mean(),
        "avg_days_to_delivery":  delivered["days_to_delivery"].mean(),
        "avg_review_score":      delivered["avg_review_score"].mean(),
    }


@st.cache_data(ttl=600, show_spinner=False)
def load_monthly_revenue() -> pd.DataFrame:
    orders = load_table("fct_orders")
    df = orders[
        orders["order_purchase_ts"].notna() & (orders["order_status"] != "canceled")
    ].copy()
    df["month"] = pd.to_datetime(df["order_purchase_ts"]).dt.to_period("M").dt.to_timestamp()
    monthly = (
        df.groupby("month", as_index=False)
          .agg(orders=("order_id", "count"), revenue=("payment_total", "sum"))
          .sort_values("month")
    )
    return monthly


@st.cache_data(ttl=600, show_spinner=False)
def load_top_categories(limit: int = 10) -> pd.DataFrame:
    items = load_table("fct_order_items")
    products = load_table("dim_products")[["product_id", "product_category", "category_group"]]
    joined = items.merge(products, on="product_id", how="left")
    grouped = (
        joined.groupby(["product_category", "category_group"], as_index=False)
              .agg(orders=("order_id", "nunique"), revenue=("item_total", "sum"))
              .sort_values("revenue", ascending=False)
              .head(limit)
    )
    return grouped


@st.cache_data(ttl=600, show_spinner=False)
def load_state_orders() -> pd.DataFrame:
    orders = load_table("fct_orders")
    customers = load_table("dim_customers")[["customer_id", "customer_state"]]
    joined = orders.merge(customers, on="customer_id", how="left")
    joined = joined[joined["customer_state"].notna()]
    grouped = (
        joined.groupby("customer_state", as_index=False)
              .agg(orders=("order_id", "nunique"), revenue=("payment_total", "sum"))
              .sort_values("orders", ascending=False)
    )
    return grouped


# ---------- render ----------

kpis = load_kpis()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Delivered Orders", f"{int(kpis['total_orders']):,}")
c2.metric("Revenue (BRL)", f"R$ {kpis['total_revenue']:,.0f}")
c3.metric("Avg Order Value", f"R$ {kpis['avg_order_value']:,.2f}")
c4.metric("On-Time Delivery", f"{kpis['on_time_rate']*100:.1f}%")

c5, c6, c7 = st.columns(3)
c5.metric("Unique Customers", f"{int(kpis['total_customers']):,}")
c6.metric("Avg Days to Delivery", f"{kpis['avg_days_to_delivery']:.1f}")
c7.metric("Avg Review Score", f"{kpis['avg_review_score']:.2f} / 5")

st.divider()

# Revenue trend
st.subheader("Monthly revenue & order volume")
monthly = load_monthly_revenue()
fig = px.line(
    monthly,
    x="month",
    y="revenue",
    markers=True,
    labels={"month": "", "revenue": "Revenue (BRL)"},
)
fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, width="stretch")

with st.expander("Underlying monthly numbers"):
    st.dataframe(monthly, width="stretch", hide_index=True)

st.divider()

# Top categories + state breakdown
left, right = st.columns([3, 2])

with left:
    st.subheader("Top 10 product categories by revenue")
    cats = load_top_categories(10)
    fig_cats = px.bar(
        cats.sort_values("revenue"),
        x="revenue",
        y="product_category",
        color="category_group",
        orientation="h",
        labels={"revenue": "Revenue (BRL)", "product_category": ""},
    )
    fig_cats.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="Group")
    st.plotly_chart(fig_cats, width="stretch")

with right:
    st.subheader("Orders by customer state")
    states = load_state_orders()
    fig_states = px.bar(
        states.head(15),
        x="customer_state",
        y="orders",
        labels={"customer_state": "State", "orders": "Orders"},
    )
    fig_states.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_states, width="stretch")
    st.caption(f"São Paulo (SP) accounts for {states.iloc[0]['orders'] / states['orders'].sum() * 100:.0f}% of all orders.")
