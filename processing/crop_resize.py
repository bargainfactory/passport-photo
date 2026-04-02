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

    # Target head height as percentage of output height
    head_pct_min, head_pct_max = spec["head_pct"]
    head_pct_mid = (head_pct_min + head_pct_max) / 2.0
    target_head_px = out_h_px * (head_pct_mid / 100.0)

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

    # Clamp to image bounds
    crop_left = max(0, min(crop_left, new_w - out_w_px))
    crop_top = max(0, min(crop_top, new_h - out_h_px))

    # If the image is smaller than the output, pad with background color
    if new_w < out_w_px or new_h < out_h_px:
        bg_color = spec.get("bg_color", (255, 255, 255))
        canvas = Image.new("RGB", (max(new_w, out_w_px), max(new_h, out_h_px)), bg_color)
        paste_x = (canvas.width - new_w) // 2
        paste_y = (canvas.height - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y))
        resized = canvas
        new_w, new_h = resized.size
        # Recalculate crop position on padded canvas
        cx = cx + paste_x
        scaled_eye_y = scaled_eye_y + paste_y
        crop_left = cx - out_w_px // 2
        crop_top = scaled_eye_y - int(target_eye_y)
        crop_left = max(0, min(crop_left, new_w - out_w_px))
        crop_top = max(0, min(crop_top, new_h - out_h_px))

    crop_right = crop_left + out_w_px
    crop_bottom = crop_top + out_h_px

    cropped = resized.crop((crop_left, crop_top, crop_right, crop_bottom))
    return set_dpi(cropped, dpi)


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
