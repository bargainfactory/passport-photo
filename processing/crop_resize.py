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

    Args:
        pil_image: PIL Image (RGB) with background already replaced
        face_metrics: dict from compute_face_metrics() with center_x, center_y,
                      head_height, eye_line_y, head_top_y, chin_y
        spec: dict with width_mm, height_mm, head_pct, eye_line_pct, bg_color

    Returns:
        PIL Image cropped and resized to the correct output dimensions at 300 DPI
    """
    img_w, img_h = pil_image.size

    # Target output size in pixels
    out_w_px = mm_to_px(spec["width_mm"], dpi)
    out_h_px = mm_to_px(spec["height_mm"], dpi)

    # Target head height as percentage of output height. Using the lower
    # end of the spec range (rather than the midpoint) keeps the face
    # comfortably centered with margin above the hair and below the chin
    # — the midpoint tends to look uncomfortably zoomed-in on most specs.
    head_pct_min, head_pct_max = spec["head_pct"]
    head_pct_target = head_pct_min + (head_pct_max - head_pct_min) * 0.25
    target_head_px = out_h_px * (head_pct_target / 100.0)

    # Current head height in the image
    current_head_h = face_metrics["head_height"]
    if current_head_h <= 0:
        current_head_h = img_h * 0.6  # fallback

    # Scale factor to match target head size
    scale = target_head_px / current_head_h

    # Resize the full image
    new_w = int(round(img_w * scale))
    new_h = int(round(img_h * scale))
    resized = pil_image.resize((new_w, new_h), Image.LANCZOS)

    # Scale face center coordinates
    cx = int(face_metrics["center_x"] * scale)
    cy = int(face_metrics["center_y"] * scale)

    # Position the face: center horizontally, place eyes at the right vertical position
    # Eye line should be at eye_line_pct from the bottom of the output
    eye_pct_min, eye_pct_max = spec.get("eye_line_pct", (56, 69))
    eye_pct_mid = (eye_pct_min + eye_pct_max) / 2.0
    target_eye_from_bottom = out_h_px * (eye_pct_mid / 100.0)
    target_eye_y = out_h_px - target_eye_from_bottom

    scaled_eye_y = int(face_metrics["eye_line_y"] * scale)

    # Crop box: center horizontally on face, position eye line correctly
    crop_left = cx - out_w_px // 2
    crop_top = scaled_eye_y - int(target_eye_y)

    # Enforce crown clearance: the space between the top of the output
    # and the crown of the head must equal crown_top_mm (default 3mm,
    # Canada uses 10mm). This overrides the eye-line-based position.
    crown_top_mm = spec.get("crown_top_mm", 3)
    crown_top_px = mm_to_px(crown_top_mm, dpi)
    scaled_head_top_y = int(face_metrics["head_top_y"] * scale)
    crop_top = scaled_head_top_y - crown_top_px

    # Pad with background color whenever the crop would extend past the
    # resized image bounds. This preserves correct head size & eye-line
    # placement instead of clipping the hair or shoulders when the source
    # selfie was framed tight.
    bg_color = spec.get("bg_color", (255, 255, 255))

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
        # Shift crop origin into the padded canvas
        crop_left += pad_left
        crop_top += pad_top
        new_w, new_h = canvas_w, canvas_h

    # Safety clamp (should be no-op after padding)
    crop_left = max(0, min(crop_left, new_w - out_w_px))
    crop_top = max(0, min(crop_top, new_h - out_h_px))

    crop_right = crop_left + out_w_px
    crop_bottom = crop_top + out_h_px

    cropped = resized.crop((crop_left, crop_top, crop_right, crop_bottom))
    return set_dpi(cropped, dpi)


def detect_crown_shift(image, bg_color, crown_mm, dpi=DEFAULT_DPI, tolerance=12):
    """Return the vertical pixel shift needed to place the crown at crown_mm.

    Scans the composited image (subject on solid background) to find the
    first non-background row, then returns how many pixels to shift.
    """
    target_px = mm_to_px(crown_mm, dpi)
    arr = np.array(image, dtype=np.int16)
    bg = np.array(bg_color, dtype=np.int16)

    diff = np.max(np.abs(arr - bg), axis=2)
    row_has_subject = np.any(diff > tolerance, axis=1)
    subject_rows = np.where(row_has_subject)[0]
    if len(subject_rows) == 0:
        return 0

    actual_top = int(subject_rows[0])
    shift = target_px - actual_top
    return shift if abs(shift) >= 2 else 0


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
