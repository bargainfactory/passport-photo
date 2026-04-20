"""Step 0: Country and document type selection (FIRST step in flow)."""

import streamlit as st
from config.country_specs import get_country_list, get_spec, COUNTRY_FLAGS
from utils.geo_ip import detect_currency
from config.constants import SUPPORTED_CURRENCIES


def render():
    """Render the country/document configuration step."""
    st.markdown(
        '<p class="section-label">Step 1 of 4</p>',
        unsafe_allow_html=True,
    )
    st.markdown("### Select Your Country & Document Type")
    st.write(
        "Choose the country and document type first. "
        "We will show you the exact requirements and guide you through the process."
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        country_list = get_country_list()
        country = st.selectbox(
            "Country",
            options=country_list,
            index=0,
            key="country_select",
            help="Select the country for your passport or visa photo.",
        )

    with col2:
        doc_type = st.radio(
            "Document Type",
            options=["Passport", "Visa"],
            key="doc_type_select",
            horizontal=True,
        )

    # Handle custom specs
    if country == "Other / Custom":
        st.info("Enter your custom photo specifications below.")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            custom_w = st.number_input("Width (mm)", 20, 100, 35, key="custom_w")
            custom_bg_r = st.number_input("BG Red (0-255)", 0, 255, 255, key="bg_r")
        with cc2:
            custom_h = st.number_input("Height (mm)", 20, 100, 45, key="custom_h")
            custom_bg_g = st.number_input("BG Green (0-255)", 0, 255, 255, key="bg_g")
        with cc3:
            custom_bg_b = st.number_input("BG Blue (0-255)", 0, 255, 255, key="bg_b")

        head_pct = st.slider(
            "Head height (% of photo)", 30, 90, (60, 80), key="head_pct_slider"
        )

        spec = {
            "width_mm": custom_w,
            "height_mm": custom_h,
            "bg_color": (custom_bg_r, custom_bg_g, custom_bg_b),
            "head_pct": head_pct,
            "eye_line_pct": (56, 69),
            "glasses": True,
            "headgear": False,
            "expression": "Neutral",
            "notes": "Custom specification",
        }
    else:
        spec = get_spec(country, doc_type.lower())
        if spec is None:
            st.error("Could not load specifications for this country.")
            return

    # Display specifications
    _render_spec_info(spec, country, doc_type)

    # Currency
    st.markdown("---")
    st.markdown("**Payment Currency**")
    detected = detect_currency()
    currency_options = [
        f"{code} ({symbol}) - {name}" for code, symbol, name in SUPPORTED_CURRENCIES
    ]
    default_idx = 0
    for i, (code, _, _) in enumerate(SUPPORTED_CURRENCIES):
        if code.lower() == detected:
            default_idx = i
            break

    selected_currency = st.selectbox(
        "Currency",
        options=currency_options,
        index=default_idx,
        key="currency_select",
        help="Auto-detected from your location. You can change it.",
    )
    currency_code = selected_currency.split(" ")[0].lower()

    # Store in session state
    st.session_state["country"] = country
    st.session_state["doc_type"] = doc_type.lower()
    st.session_state["spec"] = spec
    st.session_state["currency"] = currency_code

    st.markdown("")
    if st.button("Continue to Upload Photo", type="primary", use_container_width=True):
        st.session_state["step"] = 1
        st.rerun()


def _render_spec_info(spec, country, doc_type):
    """Render the specification info box."""
    flag = COUNTRY_FLAGS.get(country, "")

    glasses_text = "Allowed (if eyes clearly visible)" if spec["glasses"] else "Not allowed"
    headgear_text = "Allowed (religious/medical)" if spec["headgear"] else "Not allowed"
    glasses_mark = "&#10003;" if spec["glasses"] else "&#10007;"
    headgear_mark = "&#10003;" if spec["headgear"] else "&#10007;"

    bg = spec["bg_color"]
    bg_hex = f"#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}"
    swatch = (
        f'<span style="display:inline-block;width:14px;height:14px;'
        f"background:{bg_hex};border:1px solid #ccc;border-radius:3px;"
        f'vertical-align:middle;margin-right:4px;"></span>'
    )

    px_w = int(round(spec["width_mm"] * 300 / 25.4))
    px_h = int(round(spec["height_mm"] * 300 / 25.4))

    html = f"""<div class="spec-box">
        <div class="spec-title">&#128203; {flag} {country} &mdash; {doc_type} Photo Requirements</div>
        <b>Size:</b> {spec['width_mm']} &times; {spec['height_mm']} mm
        ({px_w} &times; {px_h} px @ 300 DPI)<br>
        <b>Background:</b> {swatch} RGB({bg[0]}, {bg[1]}, {bg[2]})<br>
        <b>Head height:</b> {spec['head_pct'][0]}&ndash;{spec['head_pct'][1]}% of photo<br>
        <b>Expression:</b> {spec['expression']}<br>
        <b>Glasses:</b> {glasses_mark} {glasses_text}<br>
        <b>Headgear:</b> {headgear_mark} {headgear_text}<br>
        <b>Notes:</b> {spec.get('notes', 'N/A')}
    </div>"""
    st.markdown(html, unsafe_allow_html=True)
