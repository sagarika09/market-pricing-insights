import streamlit as st

st.set_page_config(
    page_title="Market Pricing Insights",
    page_icon="👖",
    layout="wide",
)

from ui.components import render_sidebar
from ui.comparison import render_comparison

product, sources, condition = render_sidebar()
render_comparison(product, sources, condition)
