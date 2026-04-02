"""Step 4: Payment gate and photo download."""

import streamlit as st
from processing.print_sheet import create_print_sheet
from utils.image_helpers import pil_to_bytes, add_watermark
from config.constants import PHOTO_PRICE_DISPLAY, SUPPORTED_CURRENCIES, CURRENCY_SYMBOLS
from payment.stripe_checkout import create_checkout_session, verify_payment, is_stripe_configured


def render():
    """Render the download step with payment integration."""
    st.header("Download Your Photo")

    # Back button
    if st.button("\u2190 Back to Preview"):
        st.session_state["step"] = 2
        st.rerun()

    processed_pil = st.session_state.get("processed_pil")
    if processed_pil is None:
        st.error("No processed photo found. Please go back and process your photo.")
        return

    # Check for Stripe payment return
    _check_payment_return()

    # Layout selection
    col1, col2 = st.columns(2)
    with col1:
        layout = st.radio(
            "Photo Layout",
            options=["Single Photo", "2x2 Print Sheet (4x6\")"],
            key="layout_select",
            help="Single photo or multiple copies on a printable sheet.",
        )
    with col2:
        fmt = st.radio(
            "File Format",
            options=["JPEG", "PNG"],
            key="format_select",
            horizontal=True,
        )

    # Generate the selected output
    if "2x2" in layout:
        output_image = create_print_sheet(processed_pil, layout="2x2")
        filename = f"passport_photo_sheet.{fmt.lower()}"
    else:
        output_image = processed_pil
        filename = f"passport_photo.{fmt.lower()}"

    # Show preview (watermarked)
    preview = add_watermark(output_image, text="PREVIEW")
    st.image(preview, caption="Preview (watermark removed after payment)", use_container_width=True)

    spec = st.session_state.get("spec", {})
    st.markdown(
        f'<div class="spec-box">'
        f'<strong>Output:</strong> {spec.get("width_mm", "?")}x{spec.get("height_mm", "?")}mm '
        f'@ 300 DPI | Format: {fmt} | '
        f'Background: RGB{spec.get("bg_color", (255, 255, 255))}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Payment / Download section
    is_paid = st.session_state.get("paid", False)

    if is_paid:
        _render_download(output_image, filename, fmt)
    else:
        _render_payment(output_image, filename, fmt)


def _check_payment_return():
    """Check URL query params for Stripe payment completion."""
    params = st.query_params
    session_id = params.get("session_id")

    if session_id and not st.session_state.get("paid", False):
        if verify_payment(session_id):
            st.session_state["paid"] = True
            st.success("Payment successful! Your download is ready.")
        else:
            st.warning("Payment could not be verified. Please try again or contact support.")


def _render_payment(output_image, filename, fmt):
    """Render the payment card with Stripe checkout button."""
    currency = st.session_state.get("currency", "usd")
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), "$")

    st.markdown(
        f"""
        <div class="payment-card">
            <h3>Unlock Your Download</h3>
            <p>Your passport photo is ready! Complete payment to download without watermark.</p>
            <div class="price-tag">{PHOTO_PRICE_DISPLAY}</div>
            <p style="color: #64748B; font-size: 0.85rem;">
                Charged in {currency.upper()} via Stripe secure checkout.<br>
                One-time payment. No subscription.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    if is_stripe_configured():
        if st.button("Pay & Download", type="primary", use_container_width=True):
            with st.spinner("Redirecting to secure checkout..."):
                checkout_url = create_checkout_session(currency=currency)
                if checkout_url:
                    st.markdown(
                        f'<meta http-equiv="refresh" content="0;url={checkout_url}">',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("Failed to create checkout session. Please try again.")
    else:
        st.info(
            "Stripe is not configured. Set STRIPE_SECRET_KEY in .env or "
            "Streamlit secrets to enable payments."
        )
        st.markdown("**Demo mode: download available without payment.**")
        _render_download(output_image, filename, fmt)


def _render_download(output_image, filename, fmt):
    """Render the download buttons for the processed photo."""
    st.markdown(
        '<div class="download-section">'
        "<h3>Your Photo is Ready!</h3>"
        "</div>",
        unsafe_allow_html=True,
    )

    image_bytes = pil_to_bytes(output_image, fmt=fmt)

    mime = "image/jpeg" if fmt == "JPEG" else "image/png"
    st.download_button(
        label=f"Download {filename}",
        data=image_bytes,
        file_name=filename,
        mime=mime,
        use_container_width=True,
        type="primary",
    )

    # Also offer the other format
    other_fmt = "PNG" if fmt == "JPEG" else "JPEG"
    other_bytes = pil_to_bytes(output_image, fmt=other_fmt)
    other_filename = filename.rsplit(".", 1)[0] + f".{other_fmt.lower()}"
    other_mime = "image/png" if other_fmt == "PNG" else "image/jpeg"

    st.download_button(
        label=f"Also download as {other_fmt}",
        data=other_bytes,
        file_name=other_filename,
        mime=other_mime,
        use_container_width=True,
    )

    # Option to also get the other layout
    processed_pil = st.session_state.get("processed_pil")
    if processed_pil:
        if "2x2" not in filename:
            st.markdown("---")
            st.markdown("**Also want a print sheet?**")
            sheet = create_print_sheet(processed_pil, layout="2x2")
            sheet_bytes = pil_to_bytes(sheet, fmt=fmt)
            st.download_button(
                label="Download 2x2 Print Sheet",
                data=sheet_bytes,
                file_name=f"passport_photo_sheet.{fmt.lower()}",
                mime=mime,
                use_container_width=True,
            )
