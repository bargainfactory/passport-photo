"""Step 1: Photo upload or webcam capture with lighting tips."""

import streamlit as st
from config.country_specs import COUNTRY_FLAGS


def render():
    """Render the photo upload step with country context."""
    if st.button("Back to Country Selection"):
        st.session_state["step"] = 0
        st.rerun()

    st.markdown(
        '<p class="section-label">Step 2 of 4</p>',
        unsafe_allow_html=True,
    )
    st.markdown("### Upload Your Photo")

    # Show selected country context
    country = st.session_state.get("country", "")
    doc_type = st.session_state.get("doc_type", "passport")
    spec = st.session_state.get("spec", {})
    flag = COUNTRY_FLAGS.get(country, "")

    if country and country != "Other / Custom":
        w = spec.get("width_mm", "?")
        h = spec.get("height_mm", "?")
        st.markdown(
            f'<div class="country-tag">{flag} {country} &mdash; '
            f'{doc_type.title()} &mdash; {w}&times;{h}mm</div>',
            unsafe_allow_html=True,
        )

    # Lighting tips
    st.markdown(
        """<div class="tip-card">
        <span class="tip-icon">&#128161;</span><b>Lighting tips for best results:</b><br>
        Face the light source directly (e.g., a window or soft lamp in front of you)
        so light falls evenly across your face. This minimizes shadows under eyes, nose,
        chin, or on one side.
        <b>Avoid side lighting, overhead lights, or direct flash</b> &mdash; these create
        harsh shadows that often cause rejection.<br><br>
        <span class="tip-icon">&#9733;</span><b>Pro tips:</b> Use natural daylight if possible.
        Add a white reflector (paper, foam board, or a white towel) opposite the light source
        to fill shadows. Stand 1&ndash;2 feet in front of a plain wall. Keep your face centered
        and look straight at the camera.
        </div>""",
        unsafe_allow_html=True,
    )

    # Upload options
    st.write("Choose one option below:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Upload a File**")
        uploaded_file = st.file_uploader(
            "Choose a photo (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            key="file_uploader",
            help="Upload a clear, front-facing photo with even lighting.",
        )

    with col2:
        st.markdown("**Take a Selfie**")
        camera_photo = st.camera_input(
            "Take a photo with your webcam",
            key="camera_input",
            help="Center your face, look straight at the camera.",
        )

    # Process input
    image_bytes = None
    source = None

    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        source = "upload"
    elif camera_photo is not None:
        image_bytes = camera_photo.getvalue()
        source = "webcam"

    if image_bytes:
        st.session_state["uploaded_image"] = image_bytes
        st.session_state["image_source"] = source

        st.markdown("---")
        st.image(image_bytes, caption="Your uploaded photo", width=300)

        # Checklist reminder
        st.markdown(
            """<div class="spec-box">
            <b>&#9745; Pre-flight checklist:</b><br>
            &#10003; Face is clearly visible and front-facing<br>
            &#10003; Even lighting with no harsh shadows<br>
            &#10003; Neutral expression, eyes open<br>
            &#10003; No glasses (unless country allows)<br>
            &#10003; Plain background (we will replace it automatically)
            </div>""",
            unsafe_allow_html=True,
        )

        if st.button(
            "Process Photo",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["step"] = 2
            st.rerun()
