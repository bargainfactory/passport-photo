"""Crop, center, and resize photos to match country specifications.

Core algorithm:
1. Detect face rect and compute metrics
2. Scale image so head height matches the spec's head_pct range
3. Center on face, crop to output dimensions
4. Set DPI metadata for print-ready output
"""

from PIL import Image
import numpy as np
from config.constants import DEFAULT_DPI


def mm_to_px(mm, dpi=DEFAULT_DPI):
    """Convert millimeters to pixels at a given DPI."""
    return int(round(mm * dpi / 25.4))


def crop_and_center(pil_image, face_metrics, spec, dpi=DEFAULT_DPI):
    """Crop and resize image to match the country photo specification.

    The crop is anchored so the subject reaches the bottom of the frame.
    Any padding (when the source image is too short) appears at the top
    in the spec's background colour, never at the bottom.
    """
    img_w, img_h = pil_image.size
    out_w_px = mm_to_px(spec["width_mm"], dpi)
    out_h_px = mm_to_px(spec["height_mm"], dpi)

    head_pct_min, head_pct_max = spec["head_pct"]
    head_pct_target = head_pct_min + (head_pct_max - head_pct_min) * 0.25
    target_head_px = out_h_px * (head_pct_target / 100.0)

    current_head_h = face_metrics["head_height"]
    if current_head_h <= 0:
        current_head_h = img_h * 0.6

    scale = target_head_px / current_head_h

    new_w = int(round(img_w * scale))
    new_h = int(round(img_h * scale))
    resized = pil_image.resize((new_w, new_h), Image.LANCZOS)

    cx = int(face_metrics["center_x"] * scale)

    crop_left = cx - out_w_px // 2

    bg_color = spec.get("bg_color", (255, 255, 255))

    # Anchor the crop bottom to the actual bottom of the subject (skip
    # any background-coloured area below the body in the source).
    arr = np.array(resized, dtype=np.int16)
    bg = np.array(bg_color, dtype=np.int16)
    if arr.ndim == 3:
        diff = np.max(np.abs(arr - bg), axis=2)
    else:
        diff = np.abs(arr - 255)
    row_has_subject = np.any(diff > 12, axis=1)
    subject_rows = np.where(row_has_subject)[0]
    actual_bottom = int(subject_rows[-1]) + 1 if len(subject_rows) else new_h
    bottom_anchor = actual_bottom - out_h_px

    # Top-anchor: crop starts crown_px (plus hair buffer) above the
    # estimated head top, so the crown is never cut.  When the subject
    # is taller than the output frame, this wins over bottom-anchoring
    # — the body gets cut at the bottom rather than the head at the top.
    head_top_scaled = int(face_metrics["head_top_y"] * scale)
    crown_px = mm_to_px(spec.get("crown_top_mm") or 3, dpi)
    hair_buffer = int(target_head_px * 0.10)
    top_anchor = head_top_scaled - crown_px - hair_buffer
    crop_top = min(bottom_anchor, top_anchor)

    pad_left = max(0, -crop_left)
    pad_top = max(0, -crop_top)
    pad_right = max(0, (crop_left + out_w_px) - new_w)
    pad_bottom = max(0, (crop_top + out_h_px) - new_h)

    if pad_left or pad_top or pad_right or pad_bottom:
        canvas_w = new_w + pad_left + pad_right
        canvas_h = new_h + pad_top + pad_bottom
        canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
        canvas.paste(resized, (pad_left, pad_top))
        resized = canvas
        crop_left += pad_left
        crop_top += pad_top
        new_w, new_h = canvas_w, canvas_h

    crop_left = max(0, min(crop_left, new_w - out_w_px))
    crop_top = max(0, min(crop_top, new_h - out_h_px))

    cropped = resized.crop((crop_left, crop_top, crop_left + out_w_px, crop_top + out_h_px))
    cropped = set_dpi(cropped, dpi)

    crown_mm = spec.get("crown_top_mm")
    if crown_mm:
        cropped = ensure_crown_clearance(cropped, bg_color, crown_mm, dpi)

    return cropped


def crop_raw(pil_image, face_metrics, spec, dpi=DEFAULT_DPI):
    """Crop to spec dimensions without any edits — subject flush with bottom.

    Plain geometric crop anchored to the bottom of the source image.
    Any padding (when the source is too short) appears at the top in
    white, never at the bottom.
    """
    img_w, img_h = pil_image.size
    out_w_px = mm_to_px(spec["width_mm"], dpi)
    out_h_px = mm_to_px(spec["height_mm"], dpi)

    head_pct_min, head_pct_max = spec["head_pct"]
    head_pct_target = head_pct_min + (head_pct_max - head_pct_min) * 0.25
    target_head_px = out_h_px * (head_pct_target / 100.0)

    current_head_h = face_metrics["head_height"]
    if current_head_h <= 0:
        current_head_h = img_h * 0.6

    scale = target_head_px / current_head_h

    new_w = int(round(img_w * scale))
    new_h = int(round(img_h * scale))
    resized = pil_image.resize((new_w, new_h), Image.LANCZOS)

    cx = int(face_metrics["center_x"] * scale)
    crop_left = cx - out_w_px // 2

    # Anchor the crop bottom to the actual bottom of the subject (skip
    # any white-wall area below the body present in the source).
    arr = np.array(resized, dtype=np.int16)
    if arr.ndim == 3:
        diff = np.max(np.abs(arr - 255), axis=2)
    else:
        diff = 255 - arr
    row_has_subject = np.any(diff > 12, axis=1)
    subject_rows = np.where(row_has_subject)[0]
    actual_bottom = int(subject_rows[-1]) + 1 if len(subject_rows) else new_h
    bottom_anchor = actual_bottom - out_h_px

    # Top-anchor: detect the ACTUAL top of the subject in the scaled
    # source by scanning for the first non-white row in the column band
    # around the face. Then place the crop so that detected top sits at
    # exactly crown_px from the top of the output frame — no post-shift,
    # no synthetic padding, exact spec compliance.
    crown_px = mm_to_px(spec.get("crown_top_mm") or 3, dpi)
    fcx_min = max(0, int(face_metrics["center_x"] * scale - target_head_px * 0.6))
    fcx_max = min(new_w, int(face_metrics["center_x"] * scale + target_head_px * 0.6))
    column_band = arr[:, fcx_min:fcx_max]
    if column_band.ndim == 3:
        cb_diff = np.max(np.abs(column_band - 255), axis=2)
    else:
        cb_diff = 255 - column_band
    cb_subject = cb_diff > 12
    min_cols = max(3, int((fcx_max - fcx_min) * 0.02))
    row_count = np.sum(cb_subject, axis=1)
    detected_rows = np.where(row_count >= min_cols)[0]
    if len(detected_rows):
        actual_top_scaled = int(detected_rows[0])
        top_anchor = actual_top_scaled - crown_px
    else:
        # Fallback: estimate-based top-anchor with a hair buffer.
        head_top_scaled = int(face_metrics["head_top_y"] * scale)
        top_anchor = head_top_scaled - crown_px - int(target_head_px * 0.10)

    crop_top = min(bottom_anchor, top_anchor)
    # Cropped-only must not introduce top padding. Clamp the crop into
    # the source so the result is always a flush rectangle of source pixels.
    crop_top = max(0, crop_top)

    # No top padding in cropped-only output.
    pad_left = max(0, -crop_left)
    pad_top = 0
    pad_right = max(0, (crop_left + out_w_px) - new_w)
    pad_bottom = max(0, (crop_top + out_h_px) - new_h)

    if pad_left or pad_top or pad_right or pad_bottom:
        canvas_w = new_w + pad_left + pad_right
        canvas_h = new_h + pad_top + pad_bottom
        canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        canvas.paste(resized, (pad_left, pad_top))
        resized = canvas
        crop_left += pad_left
        crop_top += pad_top
        new_w, new_h = canvas_w, canvas_h

    crop_left = max(0, min(crop_left, new_w - out_w_px))
    crop_top = max(0, min(crop_top, new_h - out_h_px))

    cropped = resized.crop((crop_left, crop_top, crop_left + out_w_px, crop_top + out_h_px))
    cropped = set_dpi(cropped, dpi)
    # No post-shift — the subject top has already been placed at crown_px
    # from the top by the actual-top detection above.

    return cropped


def detect_crown_shift(image, bg_color, crown_mm, dpi=DEFAULT_DPI, tolerance=8):
    """Return the vertical pixel shift needed to place the crown at crown_mm.

    Scans the image to find the first row whose darkest deviation from
    the background colour is significant, treating that row as the top
    of the subject. Requires a column-density check to avoid mistaking
    a single noisy pixel for the subject — at least 0.5% of the row's
    pixels must be non-background for it to count as a real subject row.
    """
    target_px = mm_to_px(crown_mm, dpi)
    arr = np.array(image, dtype=np.int16)
    bg = np.array(bg_color, dtype=np.int16)

    diff = np.max(np.abs(arr - bg), axis=2)
    is_subject = diff > tolerance
    # Require at least 0.5% of the row width to be non-bg — single
    # speckles aren't enough.
    min_subject_cols = max(3, int(arr.shape[1] * 0.005))
    row_subject_count = np.sum(is_subject, axis=1)
    row_has_subject = row_subject_count >= min_subject_cols
    subject_rows = np.where(row_has_subject)[0]
    if len(subject_rows) == 0:
        return 0

    actual_top = int(subject_rows[0])
    shift = target_px - actual_top
    return int(shift) if shift != 0 else 0


def apply_crown_shift(image, shift, bg_color, dpi=DEFAULT_DPI):
    """Apply a vertical pixel shift to an image, filling with bg_color."""
    if shift == 0:
        return image
    w, h = image.size
    canvas = Image.new("RGB", (w, h), tuple(bg_color))
    canvas.paste(image, (0, shift))
    canvas = canvas.crop((0, 0, w, h))
    canvas.info["dpi"] = image.info.get("dpi", (dpi, dpi))
    return canvas


def ensure_crown_clearance(image, bg_color, crown_mm, dpi=DEFAULT_DPI, tolerance=12):
    """Shift the subject so the crown sits exactly crown_mm from the top."""
    shift = detect_crown_shift(image, bg_color, crown_mm, dpi, tolerance)
    return apply_crown_shift(image, shift, bg_color, dpi)


def flush_subject_bottom(image, bg_color, dpi=DEFAULT_DPI, tolerance=12):
    """Shift the subject down so it is flush with the bottom edge.

    After bg removal + compositing, the subject body may not reach the
    bottom of the frame.  This detects the gap and shifts downward,
    filling the vacated top rows with bg_color.
    """
    arr = np.array(image, dtype=np.int16)
    bg = np.array(bg_color, dtype=np.int16)

    diff = np.max(np.abs(arr - bg), axis=2)
    row_has_subject = np.any(diff > tolerance, axis=1)
    subject_rows = np.where(row_has_subject)[0]
    if len(subject_rows) == 0:
        return image

    last_subject_row = int(subject_rows[-1])
    gap = arr.shape[0] - 1 - last_subject_row
    if gap < 2:
        return image

    w, h = image.size
    canvas = Image.new("RGB", (w, h), tuple(bg_color))
    canvas.paste(image, (0, gap))
    canvas = canvas.crop((0, 0, w, h))
    canvas.info["dpi"] = image.info.get("dpi", (dpi, dpi))
    return canvas


def set_dpi(image, dpi=DEFAULT_DPI):
    """Set the DPI metadata on a PIL Image for print-ready output.

    Args:
        image: PIL Image
        dpi: Dots per inch (default 300)

    Returns:
        The same PIL Image with DPI info set (modifies in place and returns)
    """
    image.info["dpi"] = (dpi, dpi)
    return image
