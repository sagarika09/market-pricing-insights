import streamlit as st


def render_sidebar() -> str:
    st.sidebar.title("Market Pricing Insights")
    st.sidebar.markdown("**Resale Price Tracker**")
    st.sidebar.divider()
    st.sidebar.markdown("**Condition**")
    condition = st.sidebar.selectbox("Condition", ["Used", "All", "New"], index=0)
    st.sidebar.divider()
    st.sidebar.caption("Select a tab above to browse US or UK markets.")
    return condition
