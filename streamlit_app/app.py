"""Entry point — registers pages with st.navigation so labels are explicit."""

import streamlit as st

pages = [
    st.Page(
        "executive_overview.py",
        title="Executive Dashboard",
        icon="📊",
        default=True,
    ),
    st.Page(
        "delivery_operations.py",
        title="Delivery Operations",
        icon="🚚",
    ),
]

st.navigation(pages).run()
