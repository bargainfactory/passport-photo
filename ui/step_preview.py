"""Step 2: Run processing pipeline and show before/after preview with validation."""

import streamlit as st
from processing.face_detection import detect_face, detect_eyes, compute_face_metrics
from processing.background import remove_background, replace_background
from processing.crop_resize import crop_and_center
from processing.validation import validate_photo
from utils.image_helpers import (
    bytes_to_cv2,
    pil_to_cv2,
    add_watermark,
)
from config.country_specs import COUNTRY_FLAGS


def render():
    """Render the preview step with processing pipeline."""
    if st.button("Back to Upload"):
        st.session_state["step"] = 1
        st.rerun()

    st.markdown(
        '<p class="section-label">Step 3 of 4</p>',
        unsafe_allow_html=True,
    )
    st.markdown("### Preview Your Photo")

    image_bytes = st.session_state.get("uploaded_image")
    spec = st.session_state.get("spec")

    if not image_bytes or not spec:
        st.error("Missing photo or specifications. Please go back.")
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

    # Run pipeline (cached)
    spec_hash = hash(str(sorted(spec.items())) if isinstance(spec, dict) else str(spec))
    cache_key = f"processed_{hash(image_bytes)}_{spec_hash}"
    if cache_key not in st.session_state:
        _run_pipeline(image_bytes, spec, cache_key)

    result = st.session_state.get(cache_key)
    if result is None:
        return

    processed_image = result["processed_image"]
    validation_results = result["validation_results"]

    # Before / After
    st.markdown("**Before & After**")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="photo-box"><div class="photo-box-label">Original</div>',
            unsafe_allow_html=True,
        )
        st.image(image_bytes, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        watermarked = add_watermark(processed_image)
        st.markdown(
            '<div class="photo-box"><div class="photo-box-label">Processed (Preview)</div>',
            unsafe_allow_html=True,
        )
        st.image(watermarked, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Validation
    st.markdown("**Compliance Checks**")
    _render_validation(validation_results)

    failed = [v for v in validation_results if not v["passed"]]
    if failed:
        st.warning(
            f"{len(failed)} check(s) did not pass. The photo may still be usable, "
            "but consider retaking for best results."
        )
    else:
        st.success("All compliance checks passed! Your photo looks great.")

    # Store for download
    st.session_state["processed_pil"] = processed_image

    st.markdown("")
    if st.button("Continue to Download", type="primary", use_container_width=True):
        st.session_state["step"] = 3
        st.rerun()


def _run_pipeline(image_bytes, spec, cache_key):
    """Execute the full image processing pipeline."""
    progress = st.progress(0, text="Starting processing...")

    progress.progress(10, text="Detecting face...")
    image_bgr = bytes_to_cv2(image_bytes)
    if image_bgr is None:
        st.error("Failed to decode image. Please upload a valid JPEG or PNG.")
        progress.empty()
        return

    face_rect = detect_face(image_bgr)
    if face_rect is None:
        st.error(
            "**No face detected.** Please ensure your face is clearly visible, "
            "front-facing, well-lit, and not obstructed."
        )
        progress.empty()
        return

    eyes = detect_eyes(image_bgr, face_rect)
    face_metrics = compute_face_metrics(face_rect, image_bgr.shape, eyes)
    progress.progress(25, text="Face detected.")

    progress.progress(35, text="Validating photo...")
    validation_results = validate_photo(image_bgr, face_rect, face_metrics, spec)

    progress.progress(45, text="Removing background (AI processing)...")
    rgba_image = remove_background(image_bytes)
    progress.progress(75, text="Background removed.")

    progress.progress(80, text="Applying background and cropping...")
    bg_color = spec.get("bg_color", (255, 255, 255))
    rgb_image = replace_background(rgba_image, bg_color)

    rgb_bgr = pil_to_cv2(rgb_image)
    new_face = detect_face(rgb_bgr)
    if new_face is not None:
        new_eyes = detect_eyes(rgb_bgr, new_face)
        new_metrics = compute_face_metrics(new_face, rgb_bgr.shape, new_eyes)
    else:
        new_metrics = face_metrics

    processed = crop_and_center(rgb_image, new_metrics, spec)
    progress.progress(95, text="Finalizing...")

    st.session_state[cache_key] = {
        "processed_image": processed,
        "validation_results": validation_results,
    }
    progress.progress(100, text="Done!")
    progress.empty()


def _render_validation(results):
    """Render the validation checklist."""
    parts = ['<div class="val-card">']
    for item in results:
        if item["passed"]:
            parts.append(
                f'<div class="val-pass">&#10003; <b>{item["check"]}:</b> {item["message"]}</div>'
            )
        else:
            parts.append(
                f'<div class="val-fail">&#10007; <b>{item["check"]}:</b> {item["message"]}</div>'
            )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
