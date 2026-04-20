"""Step 3: Payment gate, photo download, and optional email delivery."""

import streamlit as st
from processing.print_sheet import create_print_sheet
from utils.image_helpers import pil_to_bytes, add_watermark
from config.constants import PHOTO_PRICE_DISPLAY, SUPPORTED_CURRENCIES, CURRENCY_SYMBOLS
from config.country_specs import COUNTRY_FLAGS
from payment.stripe_checkout import (
    create_checkout_session,
    verify_payment,
    is_stripe_configured,
)


def render():
    """Render the download step with payment integration."""
    if st.button("Back to Preview"):
        st.session_state["step"] = 2
        st.rerun()

    st.markdown(
        '<p class="section-label">Step 4 of 4</p>',
        unsafe_allow_html=True,
    )
    st.markdown("### Download Your Photo")

    processed_pil = st.session_state.get("processed_pil")
    if processed_pil is None:
        st.error("No processed photo found. Please go back and process your photo.")
        return

    # Country badge
    country = st.session_state.get("country", "")
    doc_type = st.session_state.get("doc_type", "passport")
    flag = COUNTRY_FLAGS.get(country, "")
    if country:
        st.markdown(
            f'<div class="country-tag">{flag} {country} &mdash; {doc_type.title()}</div>',
            unsafe_allow_html=True,
        )

    # Check payment return
    _check_payment_return()

    # Output options
    col1, col2 = st.columns(2)
    with col1:
        fmt = st.radio(
            "File Format",
            options=["JPEG", "PNG"],
            key="format_select",
            horizontal=True,
            help="JPEG for smaller file size, PNG for lossless quality.",
        )
    with col2:
        layout = st.radio(
            "Photo Layout",
            options=["Single Photo", "2x2 Print Sheet (4x6 in)"],
            key="layout_select",
            help="Single photo or 4 copies on a printable sheet.",
        )

    # Generate output
    if "2x2" in layout:
        output_image = create_print_sheet(processed_pil, layout="2x2")
        filename = f"passport_photo_sheet.{fmt.lower()}"
    else:
        output_image = processed_pil
        filename = f"passport_photo.{fmt.lower()}"

    # Watermarked preview
    preview = add_watermark(output_image, text="PREVIEW")
    st.image(preview, caption="Preview (watermark removed after payment)", use_container_width=True)

    # Output specs
    spec = st.session_state.get("spec", {})
    w_mm = spec.get("width_mm", "?")
    h_mm = spec.get("height_mm", "?")
    bg = spec.get("bg_color", (255, 255, 255))
    st.markdown(
        f'<div class="spec-box">'
        f"<b>Output:</b> {w_mm}&times;{h_mm}mm @ 300 DPI &middot; "
        f"Format: {fmt} &middot; Background: RGB({bg[0]}, {bg[1]}, {bg[2]})"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Payment or download
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
            st.success("Payment successful! Your download is ready below.")
        else:
            st.warning("Payment could not be verified. Please try again.")


def _render_payment(output_image, filename, fmt):
    """Render the payment card."""
    currency = st.session_state.get("currency", "usd")

    st.markdown(
        f"""<div class="pay-card">
            <h3>&#128274; Unlock Your Download</h3>
            <p style="color:#64748B;">Your passport photo is ready. Pay once to download.</p>
            <div class="price-big">{PHOTO_PRICE_DISPLAY}</div>
            <div class="pay-features">
                <span class="feat-check">&#10003;</span> Watermark-free high-resolution download<br>
                <span class="feat-check">&#10003;</span> 300 DPI print-ready quality<br>
                <span class="feat-check">&#10003;</span> Both JPEG and PNG formats included<br>
                <span class="feat-check">&#10003;</span> 2&times;2 print sheet option included<br>
                <span class="feat-check">&#10003;</span> One-time payment &mdash; no subscription
            </div>
            <p style="color:#94A3B8;font-size:0.8rem;">
                &#128737; Charged in {currency.upper()} via Stripe secure checkout.
            </p>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("")

    if is_stripe_configured():
        if st.button(
            f"Pay {PHOTO_PRICE_DISPLAY} and Download",
            type="primary",
            use_container_width=True,
        ):
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
            "**Demo mode:** Stripe is not configured. "
            "Set STRIPE_SECRET_KEY in secrets to enable payments."
        )
        st.write("Downloads are available without payment in demo mode.")
        _render_download(output_image, filename, fmt)


def _render_download(output_image, filename, fmt):
    """Render the download buttons."""
    st.markdown(
        '<div class="dl-section">'
        "<h3>&#10003; Your Photo is Ready</h3>"
        "<p>Download your compliant passport/visa photo below.</p>"
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

    # Alternative format
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

    # Print sheet option
    processed_pil = st.session_state.get("processed_pil")
    if processed_pil and "sheet" not in filename:
        st.markdown("---")
        st.write("**Need a print sheet?**")
        sheet = create_print_sheet(processed_pil, layout="2x2")
        sheet_bytes = pil_to_bytes(sheet, fmt=fmt)
        st.download_button(
            label="Download 2x2 Print Sheet (4x6 in)",
            data=sheet_bytes,
            file_name=f"passport_photo_sheet.{fmt.lower()}",
            mime=mime,
            use_container_width=True,
        )

    # Email option
    st.markdown("---")
    _render_email_option()


def _render_email_option():
    """Render an optional email-to-self section."""
    st.markdown(
        '<div class="email-card">'
        "<b>Email your photo</b><br>"
        "<span style='font-size:0.85rem;color:#475569;'>"
        "Want a copy sent to your email? Enter your address below.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        email = st.text_input(
            "Email address",
            placeholder="you@example.com",
            key="email_input",
            label_visibility="collapsed",
        )
    with col2:
        send_clicked = st.button("Send", key="send_email_btn")

    if send_clicked and email:
        if "@" in email and "." in email:
            st.info(
                "Email delivery requires a mail service integration (SendGrid, AWS SES). "
                "For now, please use the download button above."
            )
        else:
            st.error("Please enter a valid email address.")
