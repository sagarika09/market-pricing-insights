import streamlit as st
import plotly.express as px
import pandas as pd
from products import Product
from data.processor import fetch_product


def render_comparison(product: Product, sources: list[str], condition: str = "All") -> None:
    st.header(f"{product.brand} — {product.name}")
    st.caption(f"Condition: {condition} · Sources: {', '.join(sources) if sources else 'none selected'}")

    if not sources:
        st.warning("Select at least one source in the sidebar.")
        return

    with st.spinner("Fetching prices…"):
        df = fetch_product(product, sources, condition)

    if df.empty:
        st.info("No listings found under the ASP ceiling. Try adjusting the sources or check back later.")
        return

    # Per-source KPI breakdown
    cols = st.columns(len(sources))
    for col, source in zip(cols, sources):
        src_df = df[df["source"] == source]
        col.markdown(f"**{source}**")
        if src_df.empty:
            col.caption("No listings found")
        else:
            col.metric("Lowest", f"${src_df['price'].min():.2f}")
            col.metric("Highest", f"${src_df['price'].max():.2f}")
            col.metric("Average", f"${src_df['price'].mean():.2f}")
            col.metric("Listings Considered", len(src_df))

    st.divider()

    # Price distribution by source
    st.subheader("Price by Source")
    fig = px.box(
        df,
        x="source",
        y="price",
        color="source",
        points="all",
        hover_data=["title"],
        labels={"source": "Platform", "price": "Price (USD)"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Avg price bar chart
    st.subheader("Average Price Comparison")
    avg_by_source = df.groupby("source")["price"].mean().reset_index()
    avg_by_source.columns = ["Platform", "Avg Price (USD)"]
    bar_fig = px.bar(
        avg_by_source,
        x="Platform",
        y="Avg Price (USD)",
        color="Platform",
        text_auto=".2f",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    bar_fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(bar_fig, use_container_width=True)

    st.divider()

    # Listings table
    st.subheader("All Listings")
    display_df = df[["source", "image_url", "title", "price", "url"]].copy()
    display_df["image_url"] = display_df["image_url"].apply(
        lambda u: f'<img src="{u}" width="64" height="64" style="object-fit:cover;border-radius:4px;">'
        if u else '<div style="width:64px;height:64px;background:#f0f0f0;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#999;">No image</div>'
    )
    display_df.rename(columns={"image_url": "Image"}, inplace=True)
    display_df["price"] = display_df["price"].map("${:.2f}".format)
    display_df["url"] = display_df["url"].apply(lambda u: f'<a href="{u}" target="_blank">View</a>')
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
