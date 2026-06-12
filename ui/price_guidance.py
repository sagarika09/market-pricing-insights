import streamlit as st
from data.product_store import CATEGORIES
from automation import ebay_pricer, vinted_pricer


def _credentials_ready(region: str) -> bool:
    ss = st.session_state
    ebay_ok = bool(ss.get("ebay_username") and ss.get("ebay_password"))
    if region == "US":
        vinted_ok = bool(ss.get("vinted_us_email") and ss.get("vinted_us_password"))
    else:
        vinted_ok = bool(ss.get("vinted_uk_email") and ss.get("vinted_uk_password"))
    return ebay_ok and vinted_ok


def _render_credentials_form(region: str):
    st.markdown("#### 🔑 Enter your credentials *(session only — never stored)*")

    with st.expander("eBay credentials", expanded=not bool(st.session_state.get("ebay_username"))):
        c1, c2 = st.columns(2)
        st.session_state["ebay_username"] = c1.text_input(
            "eBay username / email",
            value=st.session_state.get("ebay_username", ""),
            key=f"ebay_user_input_{region}",
        )
        st.session_state["ebay_password"] = c2.text_input(
            "eBay password",
            type="password",
            value=st.session_state.get("ebay_password", ""),
            key=f"ebay_pass_input_{region}",
        )

    label = "UK" if region == "UK" else "US"
    site = "vinted.co.uk" if region == "UK" else "vinted.com"
    email_key = f"vinted_{region.lower()}_email"
    pass_key  = f"vinted_{region.lower()}_password"

    with st.expander(f"Vinted {label} credentials ({site})", expanded=not bool(st.session_state.get(email_key))):
        c1, c2 = st.columns(2)
        st.session_state[email_key] = c1.text_input(
            f"Vinted {label} email",
            value=st.session_state.get(email_key, ""),
            key=f"vinted_email_input_{region}",
        )
        st.session_state[pass_key] = c2.text_input(
            f"Vinted {label} password",
            type="password",
            value=st.session_state.get(pass_key, ""),
            key=f"vinted_pass_input_{region}",
        )


def render_price_guidance(region: str):
    st.divider()
    st.subheader("🔍 Price Guidance")
    st.caption(
        "Upload a photo and describe your item — we'll navigate eBay and Vinted's "
        "listing flows and capture their price guidance screens."
    )

    # ── Credentials ──────────────────────────────────────────────────────────
    _render_credentials_form(region)

    if not _credentials_ready(region):
        st.info("Enter credentials above to enable price guidance.")
        return

    st.success("✓ Credentials saved for this session.")
    st.divider()

    # ── Item details form ─────────────────────────────────────────────────────
    with st.form(key=f"price_guidance_form_{region}"):
        st.markdown("#### Item details")

        col_img, col_fields = st.columns([1, 2])

        with col_img:
            uploaded = st.file_uploader(
                "Photo (optional)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"pg_image_{region}",
            )
            if uploaded:
                st.image(uploaded, use_container_width=True)

        with col_fields:
            title = st.text_input("Item title *", placeholder="e.g. White midi skirt")
            brand = st.text_input("Brand", placeholder="e.g. M&S")
            cat_col, cond_col = st.columns(2)
            category  = cat_col.selectbox("Category", CATEGORIES, key=f"pg_cat_{region}")
            condition = cond_col.selectbox("Condition", ["Used", "New", "All"], key=f"pg_cond_{region}")
            size  = st.text_input("Size (optional)", placeholder="e.g. UK 12 / M")
            color = st.text_input("Colour (optional)", placeholder="e.g. White")

        submitted = st.form_submit_button("🔍 Get Price Guidance", use_container_width=True, type="primary")

    if not submitted:
        return

    if not title:
        st.error("Please enter an item title.")
        return

    image_bytes = uploaded.read() if uploaded else None
    if uploaded:
        uploaded.seek(0)

    # Build a descriptive title for the search
    search_title = " ".join(filter(None, [brand, title, size, color])).strip()

    ebay_marketplace   = "UK" if region == "UK" else "US"
    vinted_marketplace = region

    ebay_shot   = None
    vinted_shot = None

    col_ebay, col_vinted = st.columns(2)

    # ── eBay ──────────────────────────────────────────────────────────────────
    with col_ebay:
        site = "eBay UK" if region == "UK" else "eBay US"
        st.markdown(f"**{site}**")
        with st.spinner(f"Navigating {site} listing flow…"):
            ebay_shot = ebay_pricer.get_price_guidance(
                title=search_title,
                category=category,
                condition=condition,
                brand=brand,
                image_bytes=image_bytes,
                username=st.session_state["ebay_username"],
                password=st.session_state["ebay_password"],
                marketplace=ebay_marketplace,
            )
        if ebay_shot:
            st.image(ebay_shot, use_container_width=True, caption=f"{site} — Price Guidance")
        else:
            st.error(f"Could not capture {site} price guidance. Check credentials or try again.")

    # ── Vinted ────────────────────────────────────────────────────────────────
    with col_vinted:
        vsite = "Vinted UK" if region == "UK" else "Vinted US"
        st.markdown(f"**{vsite}**")
        email_key = f"vinted_{region.lower()}_email"
        pass_key  = f"vinted_{region.lower()}_password"
        with st.spinner(f"Navigating {vsite} listing flow…"):
            vinted_shot = vinted_pricer.get_price_guidance(
                title=search_title,
                category=category,
                condition=condition,
                brand=brand,
                image_bytes=image_bytes,
                email=st.session_state[email_key],
                password=st.session_state[pass_key],
                marketplace=vinted_marketplace,
            )
        if vinted_shot:
            st.image(vinted_shot, use_container_width=True, caption=f"{vsite} — Price Guidance")
        else:
            st.error(f"Could not capture {vsite} price guidance. Check credentials or try again.")
