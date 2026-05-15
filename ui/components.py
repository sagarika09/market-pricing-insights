import streamlit as st
from products import PRODUCTS, Product
from scrapers import ALL_SCRAPERS
from typing import Tuple, List


def render_sidebar() -> Tuple[Product, List[str], str]:
    st.sidebar.title("Market Pricing Insights")
    st.sidebar.markdown("**Women's Jeans — Resale Tracker**")
    st.sidebar.divider()

    product_labels = [f"{p.brand} — {p.name}" for p in PRODUCTS]
    selected_label = st.sidebar.selectbox("Product", product_labels)
    product = PRODUCTS[product_labels.index(selected_label)]

    st.sidebar.divider()
    st.sidebar.markdown("**Sources**")
    all_source_names = [s.name for s in ALL_SCRAPERS]
    selected_sources = [
        name for name in all_source_names
        if st.sidebar.checkbox(name, value=True, key=f"src_{name}")
    ]

    st.sidebar.divider()
    st.sidebar.markdown("**Condition**")
    condition = st.sidebar.selectbox("Condition", ["Used", "All", "New"], index=0)

    st.sidebar.divider()
    st.sidebar.caption(f"ASP ceiling: ${product.asp_max:.0f}")

    return product, selected_sources, condition
