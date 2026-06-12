import streamlit as st

st.set_page_config(
    page_title="Market Pricing Insights",
    page_icon="👖",
    layout="wide",
)

from ui.components import render_sidebar
from ui.comparison import render_comparison
from ui.price_guidance import render_price_guidance

condition = render_sidebar()

tab_us, tab_uk = st.tabs(["🇺🇸 US Market", "🇬🇧 UK Market"])

with tab_us:
    render_comparison(region="US", condition=condition)
    render_price_guidance(region="US")

with tab_uk:
    render_comparison(region="UK", condition=condition)
    render_price_guidance(region="UK")
