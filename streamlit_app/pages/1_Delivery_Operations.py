"""Delivery operations — on-time rate, delivery time, late shipments."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import load_table

st.set_page_config(
    page_title="Delivery Operations — Olist",
    page_icon="🚚",
    layout="wide",
)

st.title("Delivery Operations")
st.caption("On-time performance, delivery times, and late-shipment patterns across states and sellers")


# ---------- shared loader ----------

@st.cache_data(ttl=600, show_spinner="Loading delivery data...")
def load_delivered_orders() -> pd.DataFrame:
    orders = load_table("fct_orders")
    customers = load_table("dim_customers")[["customer_id", "customer_state"]]
    df = orders.merge(customers, on="customer_id", how="left")
    return df[
        (df["order_status"] == "delivered")
        & df["days_to_delivery"].notna()
        & df["delivered_on_time"].notna()
    ].copy()


df = load_delivered_orders()

# ---------- KPI tiles ----------

c1, c2, c3, c4 = st.columns(4)
c1.metric("Delivered Orders", f"{len(df):,}")
c2.metric("On-Time Rate", f"{df['delivered_on_time'].astype(float).mean()*100:.1f}%")
c3.metric("Avg Days to Delivery", f"{df['days_to_delivery'].mean():.1f}")
c4.metric("Median Days to Delivery", f"{df['days_to_delivery'].median():.1f}")

c5, c6, c7 = st.columns(3)
late = df[df["days_late_vs_estimate"] > 0]
c5.metric("Late Shipments", f"{len(late):,}", f"{len(late)/len(df)*100:.1f}% of orders")
c6.metric("Avg Days Late (when late)", f"{late['days_late_vs_estimate'].mean():.1f}")
c7.metric("Avg Hours to Approval", f"{df['hours_to_approval'].mean():.1f}")

st.divider()

# ---------- Delivery time distribution ----------

st.subheader("Days to delivery — distribution")
fig_hist = px.histogram(
    df[df["days_to_delivery"] <= 60],
    x="days_to_delivery",
    nbins=60,
    labels={"days_to_delivery": "Days from purchase to delivery", "count": "Orders"},
)
fig_hist.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), bargap=0.02)
st.plotly_chart(fig_hist, width="stretch")
st.caption(f"Tail trimmed at 60 days for readability — {(df['days_to_delivery'] > 60).sum():,} orders ({(df['days_to_delivery'] > 60).mean()*100:.1f}%) took longer.")

st.divider()

# ---------- On-time rate by state ----------

left, right = st.columns(2)

with left:
    st.subheader("On-time delivery rate by state")
    state_perf = (
        df.groupby("customer_state", as_index=False)
          .agg(
              orders=("order_id", "count"),
              on_time_rate=("delivered_on_time", lambda s: s.astype(float).mean()),
              avg_days=("days_to_delivery", "mean"),
          )
          .sort_values("orders", ascending=False)
          .head(15)
    )
    state_perf["on_time_pct"] = (state_perf["on_time_rate"] * 100).round(1)
    fig_state = px.bar(
        state_perf.sort_values("on_time_pct"),
        x="on_time_pct",
        y="customer_state",
        orientation="h",
        labels={"on_time_pct": "On-time rate (%)", "customer_state": "State"},
        text="on_time_pct",
        hover_data={"orders": True, "avg_days": ":.1f"},
    )
    fig_state.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_state.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    fig_state.update_xaxes(range=[0, 105])
    st.plotly_chart(fig_state, width="stretch")
    st.caption("Top 15 states by order volume.")

with right:
    st.subheader("Avg days to delivery by state")
    fig_days = px.bar(
        state_perf.sort_values("avg_days", ascending=False),
        x="avg_days",
        y="customer_state",
        orientation="h",
        labels={"avg_days": "Avg days to delivery", "customer_state": "State"},
        text="avg_days",
        color="avg_days",
        color_continuous_scale="reds",
    )
    fig_days.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_days.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig_days, width="stretch")
    st.caption("Northern states (RR, AP, AM) consistently take longer.")

st.divider()

# ---------- Late shipment buckets ----------

st.subheader("How late are the late shipments?")

bins = [-np.inf, 0, 3, 7, 14, 30, np.inf]
labels = ["On-time / early", "1–3 days late", "4–7 days late", "8–14 days late", "15–30 days late", "30+ days late"]
df["late_bucket"] = pd.cut(df["days_late_vs_estimate"], bins=bins, labels=labels)
bucket_counts = (
    df["late_bucket"]
      .value_counts()
      .reindex(labels)
      .reset_index()
)
bucket_counts.columns = ["bucket", "orders"]
bucket_counts["share"] = bucket_counts["orders"] / bucket_counts["orders"].sum() * 100

fig_buckets = px.bar(
    bucket_counts,
    x="bucket",
    y="orders",
    text="share",
    labels={"bucket": "", "orders": "Orders"},
    color="bucket",
    color_discrete_sequence=["#2ca02c", "#fcdc3b", "#fc9b3b", "#fc6c3b", "#d62728", "#8b0000"],
)
fig_buckets.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_buckets.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
st.plotly_chart(fig_buckets, width="stretch")

st.divider()

# ---------- Worst sellers ----------

st.subheader("Sellers with the worst on-time rate (min 50 orders)")
items = load_table("fct_order_items")
joined = items.merge(
    df[["order_id", "delivered_on_time", "days_to_delivery"]],
    on="order_id",
    how="inner",
)
seller_perf = (
    joined.groupby("seller_id", as_index=False)
          .agg(
              orders=("order_id", "nunique"),
              on_time_rate=("delivered_on_time", lambda s: s.astype(float).mean()),
              avg_days=("days_to_delivery", "mean"),
          )
)
seller_perf = seller_perf[seller_perf["orders"] >= 50].copy()
seller_perf["on_time_pct"] = (seller_perf["on_time_rate"] * 100).round(1)
worst = seller_perf.nsmallest(15, "on_time_rate")[["seller_id", "orders", "on_time_pct", "avg_days"]]
worst["avg_days"] = worst["avg_days"].round(1)
worst.columns = ["Seller ID", "Orders", "On-time %", "Avg days to delivery"]
st.dataframe(worst, width="stretch", hide_index=True)
