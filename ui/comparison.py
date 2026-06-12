import streamlit as st
import plotly.express as px
import pandas as pd
from products import Product, US_SOURCES, UK_SOURCES
from data.processor import fetch_product
from data.product_store import load_products, add_product, update_product, delete_product, CATEGORIES

_CURRENCY_SYMBOL = {"USD": "$", "GBP": "£"}

_PLATFORM_COLORS = {
    "eBay US":    "#E53238",
    "eBay UK":    "#0064D2",
    "Vinted US":  "#09B1BA",
    "Vinted UK":  "#007A80",
    "Poshmark US": "#E8143B",
}

_PLATFORM_LOGO_HTML = {
    "eBay US": (
        '<span style="font-family:\'Arial Black\',Arial,sans-serif;font-weight:900;font-size:24px;line-height:1;letter-spacing:-1px;">'
        '<span style="color:#E53238;">e</span>'
        '<span style="color:#0064D2;">B</span>'
        '<span style="color:#F5AF02;">a</span>'
        '<span style="color:#86B817;">y</span>'
        '<span style="color:#E53238;font-size:16px;"> US</span>'
        '</span>'
    ),
    "eBay UK": (
        '<span style="font-family:\'Arial Black\',Arial,sans-serif;font-weight:900;font-size:24px;line-height:1;letter-spacing:-1px;">'
        '<span style="color:#E53238;">e</span>'
        '<span style="color:#0064D2;">B</span>'
        '<span style="color:#F5AF02;">a</span>'
        '<span style="color:#86B817;">y</span>'
        '<span style="color:#0064D2;font-size:16px;"> UK</span>'
        '</span>'
    ),
    "Vinted US": (
        '<span style="font-family:Arial,sans-serif;font-weight:700;font-size:24px;'
        'color:#09B1BA;line-height:1;letter-spacing:-0.5px;">vinted <span style="font-size:16px;">US</span></span>'
    ),
    "Vinted UK": (
        '<span style="font-family:Arial,sans-serif;font-weight:700;font-size:24px;'
        'color:#007A80;line-height:1;letter-spacing:-0.5px;">vinted <span style="font-size:16px;">UK</span></span>'
    ),
    "Poshmark US": (
        '<span style="font-family:Arial,sans-serif;font-weight:700;font-size:21px;'
        'color:#E8143B;line-height:1;">Poshmark US</span>'
    ),
}

_BADGE_LOGO_HTML = {
    "eBay US": (
        '<span style="font-family:\'Arial Black\',Arial,sans-serif;font-weight:900;font-size:13px;letter-spacing:-0.5px;">'
        '<span style="color:#fff;">eBay US</span></span>'
    ),
    "eBay UK": (
        '<span style="font-family:\'Arial Black\',Arial,sans-serif;font-weight:900;font-size:13px;letter-spacing:-0.5px;">'
        '<span style="color:#fff;">eBay UK</span></span>'
    ),
    "Vinted US":  '<span style="font-family:Arial,sans-serif;font-weight:700;font-size:12px;color:#fff;">vinted US</span>',
    "Vinted UK":  '<span style="font-family:Arial,sans-serif;font-weight:700;font-size:12px;color:#fff;">vinted UK</span>',
    "Poshmark US": '<span style="font-family:Arial,sans-serif;font-weight:700;font-size:12px;color:#fff;">Poshmark US</span>',
}


def _product_form(region: str, existing: Product | None = None) -> Product | None:
    """Render add/edit form. Returns a Product on submit, None on cancel."""
    currency = "GBP" if region == "UK" else "USD"
    sym = _CURRENCY_SYMBOL[currency]
    is_edit = existing is not None

    with st.form(key=f"product_form_{region}_{is_edit}"):
        st.markdown(f"### {'Edit' if is_edit else 'Add'} Product")
        c1, c2 = st.columns(2)
        brand = c1.text_input("Brand *", value=existing.brand if existing else "")
        name  = c2.text_input("Name *",  value=existing.name  if existing else "")

        keywords_raw = st.text_area(
            "Keywords (one per line) *",
            value="\n".join(existing.keywords) if existing else "",
            height=80,
        )

        c3, c4 = st.columns(2)
        asp_max = c3.number_input(
            f"ASP Ceiling ({sym}) *",
            min_value=0.0, step=5.0,
            value=float(existing.asp_max) if existing else 50.0,
        )
        category = c4.selectbox(
            "Category",
            CATEGORIES,
            index=CATEGORIES.index(existing.category) if existing and existing.category in CATEGORIES else 0,
        )

        c5, c6, c7 = st.columns(3)
        material  = c5.text_input("Material",  value=existing.material  if existing else "")
        style     = c6.text_input("Style",     value=existing.style     if existing else "")
        condition = c7.selectbox(
            "Default Condition",
            ["Used", "All", "New"],
            index=["Used", "All", "New"].index(existing.condition) if existing and existing.condition in ["Used","All","New"] else 0,
        )

        submitted = st.form_submit_button("💾 Save", use_container_width=True)

    cancelled = st.button("Cancel", key=f"cancel_{region}_{is_edit}")
    if cancelled:
        return None

    if submitted:
        keywords = [k.strip() for k in keywords_raw.splitlines() if k.strip()]
        if not brand or not name or not keywords:
            st.error("Brand, Name, and at least one Keyword are required.")
            return None
        return Product(
            brand=brand, name=name, keywords=keywords,
            asp_max=asp_max, category=category, material=material,
            style=style, condition=condition,
            region=region, currency=currency,
        )
    return None


def _render_manage_products(region: str):
    mode_key    = f"mgmt_mode_{region}"
    edit_idx_key = f"mgmt_edit_idx_{region}"

    if mode_key not in st.session_state:
        st.session_state[mode_key] = "list"

    mode = st.session_state[mode_key]

    products = load_products(region)

    if mode == "list":
        if not products:
            st.info("No products yet. Add one below.")
        for i, p in enumerate(products):
            c1, c2, c3 = st.columns([5, 1, 1])
            sym = _CURRENCY_SYMBOL["GBP" if region == "UK" else "USD"]
            c1.markdown(
                f"**{p.brand}** — {p.name} &nbsp; "
                f'<span style="color:#888;font-size:12px;">{p.category} · ASP {sym}{p.asp_max:.0f} · {p.condition}</span>',
                unsafe_allow_html=True,
            )
            if c2.button("Edit", key=f"edit_{region}_{i}", use_container_width=True):
                st.session_state[mode_key] = "edit"
                st.session_state[edit_idx_key] = i
                st.rerun()
            if c3.button("Delete", key=f"del_{region}_{i}", use_container_width=True, type="secondary"):
                delete_product(region, i)
                st.success(f"Deleted **{p.name}**.")
                st.rerun()

        st.divider()
        if st.button("➕ Add Product", key=f"add_btn_{region}", use_container_width=True):
            st.session_state[mode_key] = "add"
            st.rerun()

    elif mode == "add":
        new_product = _product_form(region)
        if new_product:
            add_product(new_product)
            st.session_state[mode_key] = "list"
            st.success(f"Added **{new_product.name}**.")
            st.rerun()
        if st.session_state.get(mode_key) == "list":
            st.rerun()

    elif mode == "edit":
        idx = st.session_state.get(edit_idx_key, 0)
        products = load_products(region)
        if idx >= len(products):
            st.session_state[mode_key] = "list"
            st.rerun()
        updated = _product_form(region, existing=products[idx])
        if updated:
            update_product(region, idx, updated)
            st.session_state[mode_key] = "list"
            st.success(f"Updated **{updated.name}**.")
            st.rerun()
        if st.session_state.get(mode_key) == "list":
            st.rerun()


def render_comparison(region: str, condition: str) -> None:
    sources = US_SOURCES if region == "US" else UK_SOURCES
    region_products = load_products(region)

    if not region_products:
        st.info("No products configured for this region.")
        with st.expander("📦 Manage Products", expanded=True):
            _render_manage_products(region)
        return

    product_labels = [f"{p.brand} — {p.name}" for p in region_products]
    selected_label = st.selectbox(
        "Product",
        product_labels,
        key=f"product_{region}",
    )
    product = region_products[product_labels.index(selected_label)]
    sym = _CURRENCY_SYMBOL.get(product.currency, "$")

    st.header(f"{product.brand} — {product.name}")
    st.caption(
        f"Condition: {condition or product.condition} · "
        f"Sources: {', '.join(sources)} · "
        f"ASP ceiling: {sym}{product.asp_max:.0f}"
    )

    effective_condition = condition or product.condition

    with st.spinner("Fetching prices…"):
        df = fetch_product(product, sources, effective_condition)

    if df.empty:
        st.info("No listings found under the ASP ceiling. Try adjusting the condition or check back later.")
        return

    platform_order = [s for s in sources if s in df["source"].unique()]

    # ── Section 1: Market Platform Summary ──────────────────────────────────
    st.subheader("Market Platform Summary")
    st.html(_build_platform_summary(df, platform_order, sym))
    st.divider()

    # ── Section 2: Price by Source ───────────────────────────────────────────
    st.subheader("Price by Source")
    chart_type = st.radio(
        "chart_type",
        ["Box Plot", "Scatter Plot"],
        horizontal=True,
        label_visibility="collapsed",
        key=f"chart_{region}",
    )
    price_label = f"Price ({product.currency})"

    if chart_type == "Box Plot":
        fig = px.box(df, x="source", y="price", color="source", points="all",
                     hover_data=["title"],
                     labels={"source": "Platform", "price": price_label},
                     color_discrete_map=_PLATFORM_COLORS,
                     category_orders={"source": platform_order})
    else:
        fig = px.strip(df, x="source", y="price", color="source",
                       hover_data=["title"],
                       labels={"source": "Platform", "price": price_label},
                       color_discrete_map=_PLATFORM_COLORS,
                       category_orders={"source": platform_order})

    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # ── Section 3: Average Price Comparison + Executive Takeaways ────────────
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
        avg_by_source.columns = ["Platform", f"Avg Price ({product.currency})"]
        bar_fig = px.bar(
            avg_by_source, x="Platform", y=f"Avg Price ({product.currency})",
            color="Platform", text_auto=".2f",
            color_discrete_map=_PLATFORM_COLORS,
            category_orders={"Platform": platform_order},
        )
        bar_fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(bar_fig, use_container_width=True)

    with right_col:
        st.subheader("Executive Takeaways")
        st.html(_build_executive_takeaways(df, platform_order, sym))

    st.divider()

    # ── All Listings ─────────────────────────────────────────────────────────
    st.subheader("All Listings")
    df["_rank"] = df["source"].map({s: i for i, s in enumerate(sources)}).fillna(99)
    df = df.sort_values(["_rank", "price"]).drop(columns=["_rank"]).reset_index(drop=True)
    st.html(_build_card_grid(df, product.asp_max, sym))

    # ── Product Management ────────────────────────────────────────────────────
    st.divider()
    with st.expander("📦 Manage Products"):
        _render_manage_products(region)


def _build_platform_summary(df: pd.DataFrame, platform_order: list, sym: str) -> str:
    cards_html = ""
    for source in platform_order:
        src_df = df[df["source"] == source]
        color = _PLATFORM_COLORS.get(source, "#888")
        logo_html = _PLATFORM_LOGO_HTML.get(source, f'<span style="font-weight:700;font-size:20px;">{source}</span>')

        header = f"""
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;min-height:36px;">
            {logo_html}
          </div>"""

        if src_df.empty:
            cards_html += f"""
            <div style="background:#fff;border-radius:16px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
              {header}
              <div style="color:#aaa;font-size:13px;margin-top:8px;">No listings found</div>
            </div>"""
            continue

        lowest  = src_df["price"].min()
        median  = src_df["price"].median()
        highest = src_df["price"].max()
        count   = len(src_df)
        spread  = highest - lowest

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
            <div style="font-size:28px;font-weight:800;color:#1a1a2e;line-height:1.1;">{sym}{lowest:.2f}</div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:10px;">
            <div>
              <div style="font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:0.5px;">Median</div>
              <div style="font-size:20px;font-weight:700;color:#333;">{sym}{median:.2f}</div>
              <div style="font-size:11px;color:#aaa;margin-top:2px;">{count} listing{'s' if count != 1 else ''}</div>
            </div>
            <div style="display:flex;align-items:flex-end;gap:3px;height:50px;padding-bottom:2px;">
              {mini_bars}
            </div>
          </div>
          <div style="margin-top:12px;padding-top:12px;border-top:1px solid #f0f0f0;">
            <div style="font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:0.5px;">Price Spread</div>
            <div style="font-size:14px;font-weight:600;color:#555;margin-top:2px;">
              {sym}{spread:.2f}
              <span style="font-weight:400;color:#aaa;font-size:12px;">&nbsp;({sym}{lowest:.2f} – {sym}{highest:.2f})</span>
            </div>
          </div>
        </div>"""

    cols = len(platform_order) or 1
    return f"""
    <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:20px;margin-bottom:4px;">
      {cards_html}
    </div>"""


def _build_executive_takeaways(df: pd.DataFrame, platform_order: list, sym: str) -> str:
    insights = []
    platform_medians = {
        s: df[df["source"] == s]["price"].median()
        for s in platform_order
        if not df[df["source"] == s].empty
    }

    if platform_medians:
        cheapest = min(platform_medians, key=platform_medians.get)
        priciest = max(platform_medians, key=platform_medians.get)
        insights.append(f"<b>{cheapest}</b> has the lowest median at <b>{sym}{platform_medians[cheapest]:.2f}</b>.")
        if cheapest != priciest:
            savings = platform_medians[priciest] - platform_medians[cheapest]
            insights.append(f"Buying on {cheapest} vs {priciest} saves ~<b>{sym}{savings:.2f}</b> at median.")

    overall_low  = df["price"].min()
    overall_high = df["price"].max()
    insights.append(f"Prices range from <b>{sym}{overall_low:.2f}</b> to <b>{sym}{overall_high:.2f}</b> across all platforms.")

    for source in platform_order:
        count = len(df[df["source"] == source])
        if count > 0:
            insights.append(f"<b>{source}</b> has <b>{count}</b> listing{'s' if count != 1 else ''} under the ASP ceiling.")

    p25 = df["price"].quantile(0.25)
    bottom_df = df[df["price"] <= p25]
    if not bottom_df.empty:
        best = bottom_df["source"].value_counts().idxmax()
        insights.append(f"<b>{best}</b> leads in bottom-quartile deals (≤ {sym}{p25:.2f}).")

    bullets = "".join(f'<li style="margin-bottom:10px;line-height:1.5;">{txt}</li>' for txt in insights)
    return f"""
    <div style="background:#f8f9ff;border-radius:14px;padding:22px 24px;
                border-left:4px solid #1a1a2e;box-sizing:border-box;">
      <ul style="margin:0;padding-left:18px;color:#333;font-size:13px;">{bullets}</ul>
    </div>"""


def _build_card_grid(df: pd.DataFrame, asp_max: float, sym: str) -> str:
    cards_html = ""
    for _, row in df.iterrows():
        source    = row["source"]
        badge_bg  = _PLATFORM_COLORS.get(source, "#888")
        badge_logo = _BADGE_LOGO_HTML.get(source, f'<span style="font-weight:700;font-size:12px;color:#fff;">{source}</span>')
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
            <div style="font-size:17px;font-weight:800;color:#111;">{sym}{price:.2f}</div>
            <div style="font-size:12px;color:#333;margin:5px 0 4px;line-height:1.4;min-height:34px;">{title}</div>
            <div style="margin-bottom:10px;">
              <div style="font-size:10px;color:#aaa;margin-bottom:3px;">ASP Ceiling: {sym}{asp_max:.0f}</div>
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
