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

    # Per-source KPI breakdown (always eBay → Vinted → Poshmark)
    ordered_sources = [s for s in ["eBay", "Vinted", "Poshmark"] if s in sources]
    cols = st.columns(len(ordered_sources))
    for col, source in zip(cols, ordered_sources):
        src_df = df[df["source"] == source]
        col.markdown(f"**{source}**")
        if src_df.empty:
            col.caption("No listings found")
        else:
            col.metric("Lowest", f"${src_df['price'].min():.2f}")
            col.metric("Highest", f"${src_df['price'].max():.2f}")
            col.metric("Median", f"${src_df['price'].median():.2f}")
            col.metric("Listings Considered", len(src_df))

    st.divider()

    platform_order = [s for s in ["eBay", "Vinted", "Poshmark"] if s in sources]

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
        category_orders={"source": platform_order},
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Avg price bar chart
    st.subheader("Average Price Comparison")
    avg_by_source = df.groupby("source")["price"].mean().reindex(platform_order).dropna().reset_index()
    avg_by_source.columns = ["Platform", "Avg Price (USD)"]
    bar_fig = px.bar(
        avg_by_source,
        x="Platform",
        y="Avg Price (USD)",
        color="Platform",
        text_auto=".2f",
        color_discrete_sequence=px.colors.qualitative.Set2,
        category_orders={"Platform": platform_order},
    )
    bar_fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(bar_fig, use_container_width=True)

    st.divider()

    # Listings card grid
    st.subheader("All Listings")
    source_order = ["eBay", "Vinted", "Poshmark"]
    df["_source_rank"] = df["source"].map({s: i for i, s in enumerate(source_order)}).fillna(99)
    df = df.sort_values(["_source_rank", "price"]).drop(columns=["_source_rank"]).reset_index(drop=True)
    st.html(_build_card_grid(df, product.asp_max))


_BADGE_STYLE = {
    "eBay":     ("🛒", "#E53238", "#fff"),
    "Vinted":   ("V",  "#09B1BA", "#fff"),
    "Poshmark": ("P",  "#E8143B", "#fff"),
}

def _build_card_grid(df: pd.DataFrame, asp_max: float) -> str:
    cards_html = ""
    for _, row in df.iterrows():
        source = row["source"]
        icon, badge_bg, badge_fg = _BADGE_STYLE.get(source, ("•", "#888", "#fff"))
        price = row["price"]
        title = str(row["title"])[:80]
        url = row["url"]
        image_url = row.get("image_url", "")
        asp_pct = min(100, round((price / asp_max) * 100)) if asp_max else 0

        img_html = (
            f'<img src="{image_url}" style="width:100%;aspect-ratio:1;object-fit:cover;">'
            if image_url else
            '<div style="width:100%;aspect-ratio:1;background:#f5f5f5;display:flex;align-items:center;justify-content:center;color:#bbb;font-size:28px;">🖼</div>'
        )

        cards_html += f"""
        <div style="background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.09);display:flex;flex-direction:column;">
          <div style="position:relative;">
            {img_html}
            <div style="position:absolute;top:10px;left:10px;background:{badge_bg};color:{badge_fg};border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700;letter-spacing:0.3px;">
              {icon} {source}
            </div>
          </div>
          <div style="padding:12px;display:flex;flex-direction:column;flex:1;">
            <div style="font-size:17px;font-weight:800;color:#111;">${price:.2f}</div>
            <div style="font-size:12px;color:#333;margin:5px 0 4px;line-height:1.4;min-height:34px;">{title}</div>
            <div style="font-size:11px;color:#888;margin-bottom:8px;">Used</div>
            <div style="margin-bottom:10px;">
              <div style="font-size:10px;color:#aaa;margin-bottom:3px;">ASP Ceiling: ${asp_max:.0f}</div>
              <div style="background:#eee;border-radius:4px;height:4px;">
                <div style="background:#1a1a2e;width:{asp_pct}%;height:100%;border-radius:4px;"></div>
              </div>
            </div>
            <a href="{url}" target="_blank" style="display:block;text-align:center;background:#1a1a2e;color:#fff;padding:8px 0;border-radius:8px;text-decoration:none;font-size:12px;font-weight:700;letter-spacing:0.5px;margin-top:auto;">VIEW LISTING</a>
          </div>
        </div>"""

    return f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;padding:4px 0 20px;">
      {cards_html}
    </div>"""
