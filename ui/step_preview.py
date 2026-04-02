"""Step 3: Run processing pipeline and show before/after preview with validation."""

import streamlit as st
from processing.face_detection import detect_face, detect_eyes, compute_face_metrics
from processing.background import remove_background, replace_background
from processing.crop_resize import crop_and_center
from processing.validation import validate_photo
from utils.image_helpers import (
    bytes_to_cv2,
    bytes_to_pil,
    cv2_to_pil,
    pil_to_cv2,
    pil_to_bytes,
    add_watermark,
)


def render():
    """Render the preview step with processing pipeline."""
    st.header("Preview Your Photo")

    # Back button
    if st.button("\u2190 Back to Settings"):
        st.session_state["step"] = 1
        st.rerun()

    image_bytes = st.session_state.get("uploaded_image")
    spec = st.session_state.get("spec")

    if not image_bytes or not spec:
        st.error("Missing photo or specifications. Please go back.")
        return

    # Run processing pipeline (only if not already processed for this image)
    cache_key = f"processed_{hash(image_bytes)}"
    if cache_key not in st.session_state:
        _run_pipeline(image_bytes, spec, cache_key)

    result = st.session_state.get(cache_key)
    if result is None:
        return

    processed_image = result["processed_image"]
    validation_results = result["validation_results"]

    # Before / After comparison
    st.subheader("Before & After")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="photo-container">', unsafe_allow_html=True)
        st.image(image_bytes, caption="Original", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Show watermarked preview
        watermarked = add_watermark(processed_image)
        st.markdown('<div class="photo-container">', unsafe_allow_html=True)
        st.image(watermarked, caption="Processed (Preview)", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Validation checklist
    st.subheader("Compliance Checks")
    _render_validation(validation_results)

    # Warnings
    failed = [v for v in validation_results if not v["passed"]]
    if failed:
        st.warning(
            "Some checks did not pass. The photo may still be usable, "
            "but consider retaking for best results."
        )

    # Store clean processed image for download
    st.session_state["processed_pil"] = processed_image

    # Continue button
    st.markdown("")
    if st.button("Continue to Download \u2192", type="primary", use_container_width=True):
        st.session_state["step"] = 3
        st.rerun()


def _run_pipeline(image_bytes, spec, cache_key):
    """Execute the full image processing pipeline."""
    with st.spinner("Detecting face..."):
        image_bgr = bytes_to_cv2(image_bytes)
        if image_bgr is None:
            st.error("Failed to decode image. Please upload a valid JPEG or PNG.")
            return

        face_rect = detect_face(image_bgr)
        if face_rect is None:
            st.error(
                "No face detected in the photo. Please ensure:\n"
                "- Your face is clearly visible and front-facing\n"
                "- The photo is well-lit\n"
                "- There are no obstructions covering your face"
            )
            return

        eyes = detect_eyes(image_bgr, face_rect)
        face_metrics = compute_face_metrics(face_rect, image_bgr.shape, eyes)

    # Validate original photo
    validation_results = validate_photo(image_bgr, face_rect, face_metrics, spec)

    with st.spinner("Removing background (this may take a moment)..."):
        rgba_image = remove_background(image_bytes)

    with st.spinner("Applying background and cropping..."):
        bg_color = spec.get("bg_color", (255, 255, 255))
        rgb_image = replace_background(rgba_image, bg_color)

        # Re-detect face on the new image for accurate cropping
        rgb_bgr = pil_to_cv2(rgb_image)
        new_face = detect_face(rgb_bgr)
        if new_face is not None:
            new_eyes = detect_eyes(rgb_bgr, new_face)
            new_metrics = compute_face_metrics(new_face, rgb_bgr.shape, new_eyes)
        else:
            # Fallback to original metrics scaled proportionally
            new_metrics = face_metrics

        processed = crop_and_center(rgb_image, new_metrics, spec)

    st.session_state[cache_key] = {
        "processed_image": processed,
        "validation_results": validation_results,
    }


def _render_validation(results):
    """Render the validation checklist as styled HTML."""
    for item in results:
        if item["passed"]:
            icon = "\u2705"
            css_class = "check-pass"
        else:
            icon = "\u274c"
            css_class = "check-fail"

        st.markdown(
            f'<div class="{css_class}">{icon} <strong>{item["check"]}:</strong> {item["message"]}</div>',
            unsafe_allow_html=True,
        )
