"""Olist Executive Overview — Streamlit dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.db import query

st.set_page_config(
    page_title="Olist Executive Overview",
    page_icon="📦",
    layout="wide",
)

st.title("Olist Executive Overview")
st.caption("2016–2018 Brazilian e-commerce — orders, revenue, delivery, geography")


# ---------- data loaders ----------

@st.cache_data(ttl=600, show_spinner="Loading order metrics...")
def load_kpis() -> dict:
    df = query(
        """
        select
            count(*)                                                           as total_orders,
            count(distinct customer_id)                                        as total_customers,
            sum(payment_total)                                                 as total_revenue,
            avg(payment_total)                                                 as avg_order_value,
            avg(case when delivered_on_time then 1.0 else 0.0 end)             as on_time_rate,
            avg(days_to_delivery)                                              as avg_days_to_delivery,
            avg(avg_review_score)                                              as avg_review_score
        from fct_orders
        where order_status = 'delivered'
        """
    )
    return df.iloc[0].to_dict()


@st.cache_data(ttl=600, show_spinner=False)
def load_monthly_revenue() -> pd.DataFrame:
    return query(
        """
        select
            date_trunc('month', order_purchase_ts)::date as month,
            count(*)            as orders,
            sum(payment_total)  as revenue
        from fct_orders
        where order_purchase_ts is not null
          and order_status <> 'canceled'
        group by 1
        order by 1
        """
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_top_categories(limit: int = 10) -> pd.DataFrame:
    return query(
        f"""
        select
            p.product_category,
            p.category_group,
            count(distinct oi.order_id) as orders,
            sum(oi.item_total)          as revenue
        from fct_order_items oi
        join dim_products p on oi.product_id = p.product_id
        group by 1, 2
        order by revenue desc
        limit {limit}
        """
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_state_orders() -> pd.DataFrame:
    return query(
        """
        select
            c.customer_state,
            count(distinct o.order_id) as orders,
            sum(o.payment_total)       as revenue
        from fct_orders o
        join dim_customers c on o.customer_id = c.customer_id
        where c.customer_state is not null
        group by 1
        order by orders desc
        """
    )


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
