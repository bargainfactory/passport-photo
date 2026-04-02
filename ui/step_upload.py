"""Step 1: Photo upload or webcam capture with lighting tips."""

import streamlit as st


LIGHTING_TIP = """
<div class="tip-card">
<strong>For best results with your selfie:</strong><br>
Face the light source directly (e.g., a window or soft lamp in front of you) so light
falls evenly across your face. This minimizes shadows under eyes, nose, chin, or on one
side. <strong>Avoid side lighting, overhead lights, or direct flash</strong> \u2014 these create
harsh shadows that often cause rejection. Use natural daylight if possible, and add a
white reflector (like paper or foam board) opposite the light to fill shadows.
</div>
"""


def render():
    """Render the photo upload step."""
    st.header("Upload Your Photo")

    # Prominent lighting tips
    st.markdown(LIGHTING_TIP, unsafe_allow_html=True)

    st.markdown("Choose one option below:")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Upload a File")
        uploaded_file = st.file_uploader(
            "Choose a photo (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            key="file_uploader",
            help="Upload a clear, front-facing photo with even lighting.",
        )

    with col2:
        st.subheader("Take a Selfie")
        camera_photo = st.camera_input(
            "Take a photo with your webcam",
            key="camera_input",
            help="Center your face, look straight at the camera.",
        )

    # Process whichever input was provided
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

        # Show a small preview
        st.image(image_bytes, caption="Your uploaded photo", width=300)

        if st.button("Continue to Country Selection \u2192", type="primary", use_container_width=True):
            st.session_state["step"] = 1
            st.rerun()
    else:
        # Clear any previous upload if user removed the file
        if "uploaded_image" in st.session_state and st.session_state.get("image_source"):
            pass  # Keep existing upload
