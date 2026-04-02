"""Step 2: Country and document type selection with spec display."""

import streamlit as st
from config.country_specs import get_country_list, get_spec
from utils.geo_ip import detect_currency, get_currency_display
from config.constants import SUPPORTED_CURRENCIES


def render():
    """Render the country/document configuration step."""
    st.header("Select Country & Document Type")

    # Back button
    if st.button("\u2190 Back to Upload"):
        st.session_state["step"] = 0
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        country = st.selectbox(
            "Country",
            options=get_country_list(),
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

    # Handle "Other / Custom"
    if country == "Other / Custom":
        st.info("Enter your custom photo specifications below.")
        cc1, cc2 = st.columns(2)
        with cc1:
            custom_w = st.number_input("Width (mm)", min_value=20, max_value=100, value=35, key="custom_w")
            custom_bg_r = st.number_input("Background Red (0-255)", 0, 255, 255, key="bg_r")
        with cc2:
            custom_h = st.number_input("Height (mm)", min_value=20, max_value=100, value=45, key="custom_h")
            custom_bg_g = st.number_input("Background Green (0-255)", 0, 255, 255, key="bg_g")

        custom_bg_b = st.number_input("Background Blue (0-255)", 0, 255, 255, key="bg_b")
        head_pct = st.slider("Head height (% of photo)", 30, 90, (60, 80), key="head_pct_slider")

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

    # Display specification details
    _render_spec_info(spec, country, doc_type)

    # Currency selection
    st.markdown("---")
    detected = detect_currency()
    currency_options = [f"{code} ({symbol})" for code, symbol, name in SUPPORTED_CURRENCIES]
    default_idx = 0
    for i, (code, _, _) in enumerate(SUPPORTED_CURRENCIES):
        if code.lower() == detected:
            default_idx = i
            break

    selected_currency = st.selectbox(
        "Payment Currency",
        options=currency_options,
        index=default_idx,
        key="currency_select",
        help="Auto-detected from your location. You can change it.",
    )
    # Extract currency code from "USD ($)" format
    currency_code = selected_currency.split(" ")[0].lower()

    # Store selections in session state
    st.session_state["country"] = country
    st.session_state["doc_type"] = doc_type.lower()
    st.session_state["spec"] = spec
    st.session_state["currency"] = currency_code

    # Process button
    st.markdown("")
    if st.button("Process Photo \u2192", type="primary", use_container_width=True):
        if "uploaded_image" not in st.session_state:
            st.error("No photo uploaded. Please go back and upload a photo.")
        else:
            st.session_state["step"] = 2
            st.rerun()


def _render_spec_info(spec, country, doc_type):
    """Render the specification info box."""
    glasses_str = "Allowed (if eyes clearly visible)" if spec["glasses"] else "Not allowed"
    headgear_str = "Allowed (religious/medical)" if spec["headgear"] else "Not allowed"

    bg = spec["bg_color"]
    bg_hex = f"#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}"
    bg_swatch = f'<span style="display:inline-block;width:14px;height:14px;background:{bg_hex};border:1px solid #ccc;border-radius:3px;vertical-align:middle;"></span>'

    html = f"""
    <div class="spec-box">
        <strong>{country} \u2014 {doc_type} Photo Requirements</strong><br><br>
        <strong>Size:</strong> {spec['width_mm']} x {spec['height_mm']} mm @ 300 DPI<br>
        <strong>Background:</strong> {bg_swatch} RGB({bg[0]}, {bg[1]}, {bg[2]})<br>
        <strong>Head height:</strong> {spec['head_pct'][0]}\u2013{spec['head_pct'][1]}% of photo<br>
        <strong>Expression:</strong> {spec['expression']}<br>
        <strong>Glasses:</strong> {glasses_str}<br>
        <strong>Headgear:</strong> {headgear_str}<br>
        <strong>Notes:</strong> {spec.get('notes', 'N/A')}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
