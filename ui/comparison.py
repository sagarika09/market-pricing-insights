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

    platform_order = [s for s in ["eBay", "Vinted", "Poshmark"] if s in sources]

    # ── Section 1: Market Platform Summary ────────────────────────────────
    st.subheader("Market Platform Summary")
    st.html(_build_platform_summary(df, platform_order))

    st.divider()

    # ── Section 2: Price by Source ─────────────────────────────────────────
    st.subheader("Price by Source")
    chart_type = st.radio(
        "chart_type",
        ["Box Plot", "Scatter Plot"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if chart_type == "Box Plot":
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
    else:
        fig = px.strip(
            df,
            x="source",
            y="price",
            color="source",
            hover_data=["title"],
            labels={"source": "Platform", "price": "Price (USD)"},
            color_discrete_sequence=px.colors.qualitative.Set2,
            category_orders={"source": platform_order},
        )

    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Section 3: Average Price Comparison + Executive Takeaways ──────────
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("Average Price Comparison")
        avg_by_source = (
            df.groupby("source")["price"]
            .mean()
            .reindex(platform_order)
            .dropna()
            .reset_index()
        )
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

    with right_col:
        st.subheader("Executive Takeaways")
        st.html(_build_executive_takeaways(df, platform_order))

    st.divider()

    # ── All Listings ────────────────────────────────────────────────────────
    st.subheader("All Listings")
    source_order = ["eBay", "Vinted", "Poshmark"]
    df["_source_rank"] = df["source"].map({s: i for i, s in enumerate(source_order)}).fillna(99)
    df = df.sort_values(["_source_rank", "price"]).drop(columns=["_source_rank"]).reset_index(drop=True)
    st.html(_build_card_grid(df, product.asp_max))


# ── Platform summary card grid ──────────────────────────────────────────────

_PLATFORM_COLORS = {
    "eBay":     "#E53238",
    "Vinted":   "#09B1BA",
    "Poshmark": "#E8143B",
}
_PLATFORM_ICONS = {
    "eBay":     "🛒",
    "Vinted":   "V",
    "Poshmark": "P",
}
_PLATFORM_LOGO_SVGS = {
    "eBay": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 32" height="32" role="img" aria-label="eBay">'
        '<text font-family="Arial Black,Arial,sans-serif" font-weight="900" font-size="32">'
        '<tspan x="0" y="28" fill="#E53238">e</tspan>'
        '<tspan fill="#0064D2">B</tspan>'
        '<tspan fill="#F5AF02">a</tspan>'
        '<tspan fill="#86B817">y</tspan>'
        '</text></svg>'
    ),
    "Vinted": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 32" height="32" role="img" aria-label="Vinted">'
        '<text x="0" y="25" font-family="Arial,sans-serif" font-weight="700" font-size="24" fill="#09B1BA">'
        'vinted</text></svg>'
    ),
    "Poshmark": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130 32" height="32" role="img" aria-label="Poshmark">'
        '<text x="0" y="24" font-family="Arial,sans-serif" font-weight="700" font-size="22" fill="#E8143B">'
        'Poshmark</text></svg>'
    ),
}


def _build_platform_summary(df: pd.DataFrame, platform_order: list[str]) -> str:
    cards_html = ""
    for source in platform_order:
        src_df = df[df["source"] == source]
        color = _PLATFORM_COLORS.get(source, "#888")
        icon = _PLATFORM_ICONS.get(source, "•")
        logo_svg = _PLATFORM_LOGO_SVGS.get(source, "")

        header = f"""
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;min-height:36px;">
            {logo_svg}
          </div>"""

        if src_df.empty:
            cards_html += f"""
            <div style="background:#fff;border-radius:16px;padding:24px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.08);">
              {header}
              <div style="color:#aaa;font-size:13px;margin-top:8px;">No listings found</div>
            </div>"""
            continue

        lowest  = src_df["price"].min()
        median  = src_df["price"].median()
        highest = src_df["price"].max()
        count   = len(src_df)
        spread  = highest - lowest

        # Mini histogram bars (5 buckets)
        bins = pd.cut(src_df["price"], bins=5)
        bin_counts = src_df.groupby(bins, observed=True).size().reset_index(name="n")
        max_n = bin_counts["n"].max() if not bin_counts.empty else 1
        mini_bars = "".join(
            f'<div style="background:{color};width:14px;'
            f'height:{max(4, round(row["n"] / max_n * 40))}px;'
            f'border-radius:3px 3px 0 0;opacity:0.85;"></div>'
            for _, row in bin_counts.iterrows()
        )

        cards_html += f"""
        <div style="background:#fff;border-radius:16px;padding:24px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.08);display:flex;flex-direction:column;gap:4px;">
          {header}
          <div>
            <div style="font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:0.5px;">Lowest Price</div>
            <div style="font-size:28px;font-weight:800;color:#1a1a2e;line-height:1.1;">${lowest:.2f}</div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:10px;">
            <div>
              <div style="font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:0.5px;">Median</div>
              <div style="font-size:20px;font-weight:700;color:#333;">${median:.2f}</div>
              <div style="font-size:11px;color:#aaa;margin-top:2px;">{count} listing{'s' if count != 1 else ''}</div>
            </div>
            <div style="display:flex;align-items:flex-end;gap:3px;height:50px;padding-bottom:2px;">
              {mini_bars}
            </div>
          </div>
          <div style="margin-top:12px;padding-top:12px;border-top:1px solid #f0f0f0;">
            <div style="font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:0.5px;">Price Spread</div>
            <div style="font-size:14px;font-weight:600;color:#555;margin-top:2px;">
              ${spread:.2f}
              <span style="font-weight:400;color:#aaa;font-size:12px;">&nbsp;(${lowest:.2f} – ${highest:.2f})</span>
            </div>
          </div>
        </div>"""

    cols = len(platform_order) or 1
    return f"""
    <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:20px;margin-bottom:4px;">
      {cards_html}
    </div>"""


# ── Executive takeaways panel ───────────────────────────────────────────────

def _build_executive_takeaways(df: pd.DataFrame, platform_order: list[str]) -> str:
    insights: list[str] = []

    platform_medians = {
        s: df[df["source"] == s]["price"].median()
        for s in platform_order
        if not df[df["source"] == s].empty
    }

    if platform_medians:
        cheapest = min(platform_medians, key=platform_medians.get)
        priciest = max(platform_medians, key=platform_medians.get)
        insights.append(
            f"<b>{cheapest}</b> has the lowest median at <b>${platform_medians[cheapest]:.2f}</b>."
        )
        if cheapest != priciest:
            savings = platform_medians[priciest] - platform_medians[cheapest]
            insights.append(
                f"Buying on {cheapest} vs {priciest} saves ~<b>${savings:.2f}</b> at median."
            )

    overall_low  = df["price"].min()
    overall_high = df["price"].max()
    insights.append(
        f"Prices range from <b>${overall_low:.2f}</b> to <b>${overall_high:.2f}</b> across all platforms."
    )

    for source in platform_order:
        count = len(df[df["source"] == source])
        if count > 0:
            insights.append(
                f"<b>{source}</b> has <b>{count}</b> listing{'s' if count != 1 else ''} under the ASP ceiling."
            )

    p25 = df["price"].quantile(0.25)
    bottom_df = df[df["price"] <= p25]
    if not bottom_df.empty:
        best = bottom_df["source"].value_counts().idxmax()
        insights.append(
            f"<b>{best}</b> leads in bottom-quartile deals (≤ ${p25:.2f})."
        )

    bullets = "".join(
        f'<li style="margin-bottom:10px;line-height:1.5;">{txt}</li>'
        for txt in insights
    )

    return f"""
    <div style="background:#f8f9ff;border-radius:14px;padding:22px 24px;
                border-left:4px solid #1a1a2e;box-sizing:border-box;">
      <ul style="margin:0;padding-left:18px;color:#333;font-size:13px;">
        {bullets}
      </ul>
    </div>"""


# ── Listing card grid ───────────────────────────────────────────────────────

_BADGE_STYLE = {
    "eBay":     ("#E53238", "#fff"),
    "Vinted":   ("#09B1BA", "#fff"),
    "Poshmark": ("#E8143B", "#fff"),
}

_BADGE_LOGO_SVGS = {
    "eBay": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 20" height="14" role="img">'
        '<text font-family="Arial Black,Arial,sans-serif" font-weight="900" font-size="20">'
        '<tspan x="0" y="17" fill="#E53238">e</tspan>'
        '<tspan fill="#fff">B</tspan>'
        '<tspan fill="#F5AF02">a</tspan>'
        '<tspan fill="#86B817">y</tspan>'
        '</text></svg>'
    ),
    "Vinted": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 58 18" height="13" role="img">'
        '<text x="0" y="14" font-family="Arial,sans-serif" font-weight="700" font-size="15" fill="#fff">'
        'vinted</text></svg>'
    ),
    "Poshmark": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 18" height="13" role="img">'
        '<text x="0" y="14" font-family="Arial,sans-serif" font-weight="700" font-size="14" fill="#fff">'
        'Poshmark</text></svg>'
    ),
}


def _build_card_grid(df: pd.DataFrame, asp_max: float) -> str:
    cards_html = ""
    for _, row in df.iterrows():
        source = row["source"]
        badge_bg, badge_fg = _BADGE_STYLE.get(source, ("#888", "#fff"))
        badge_logo = _BADGE_LOGO_SVGS.get(source, f'<span style="font-weight:700;">{source}</span>')
        price     = row["price"]
        title     = str(row["title"])[:80]
        url       = row["url"]
        image_url = row.get("image_url", "")
        asp_pct   = min(100, round((price / asp_max) * 100)) if asp_max else 0

        img_html = (
            f'<img src="{image_url}" style="width:100%;aspect-ratio:1;object-fit:cover;">'
            if image_url else
            '<div style="width:100%;aspect-ratio:1;background:#f5f5f5;display:flex;'
            'align-items:center;justify-content:center;color:#bbb;font-size:28px;">🖼</div>'
        )

        cards_html += f"""
        <div style="background:#fff;border-radius:14px;overflow:hidden;
                    box-shadow:0 2px 10px rgba(0,0,0,0.09);display:flex;flex-direction:column;">
          <div style="position:relative;">
            {img_html}
            <div style="position:absolute;top:10px;left:10px;background:{badge_bg};
                        border-radius:20px;padding:4px 10px;display:flex;align-items:center;">
              {badge_logo}
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
            <a href="{url}" target="_blank"
               style="display:block;text-align:center;background:#1a1a2e;color:#fff;
                      padding:8px 0;border-radius:8px;text-decoration:none;
                      font-size:12px;font-weight:700;letter-spacing:0.5px;margin-top:auto;">VIEW LISTING</a>
          </div>
        </div>"""

    return f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;padding:4px 0 20px;">
      {cards_html}
    </div>"""
