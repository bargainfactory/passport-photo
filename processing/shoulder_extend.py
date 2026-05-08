"""Extend shoulders to fill bottom and side gaps in cropped passport photos.

After cropping to spec, the subject's body may not reach the bottom or
the sides of the frame, leaving background-coloured space around the
shoulders. This module detects those gaps and fills them by extending
the clothing colours outward — `extend_shoulders` stretches downward
with a natural gradient and `extend_sides` inpaints the lateral margins
from the body's boundary outward — the same principle as Photoshop's
Content-Aware Fill.
"""

import cv2
import numpy as np
from PIL import Image


def extend_shoulders(
    pil_image: Image.Image,
    alpha_array: np.ndarray,
    bg_color_rgb: tuple,
    min_gap_pct: float = 3.0,
) -> Image.Image:
    """Fill the bottom gap by extending shoulder/clothing pixels.

    Args:
        pil_image:    Composited RGB passport photo (PIL Image).
        alpha_array:  Alpha mask from bg removal, uint8 (h, w). Used to
                      locate the bottom edge of the subject.
        bg_color_rgb: (R, G, B) background color tuple.
        min_gap_pct:  Skip extension if the gap is smaller than this
                      percentage of image height.

    Returns:
        PIL Image with shoulders extended to fill the bottom gap.
    """
    w, h = pil_image.size
    img = np.array(pil_image)

    opaque = alpha_array > 128
    if not np.any(opaque):
        return pil_image

    # --- Bottom edge detection (vectorized) ---
    row_idx = np.arange(h).reshape(-1, 1)
    bottom_edge = np.max(row_idx * opaque.astype(np.intp), axis=0)

    has_subject = np.any(opaque, axis=0)
    center = slice(w // 4, 3 * w // 4)
    valid = bottom_edge[center]
    valid = valid[valid > 0]
    if len(valid) == 0:
        return pil_image

    median_edge = int(np.median(valid))
    gap = h - median_edge
    if gap < max(8, h * min_gap_pct / 100):
        return pil_image

    # --- Sample edge colors (average of last 6 rows per column) ---
    valid_cols = np.where(has_subject)[0]
    edge_ys = bottom_edge[valid_cols]
    edge_colors = np.zeros((w, 3), dtype=np.float32)
    accum = np.zeros((len(valid_cols), 3), dtype=np.float32)
    for depth in range(6):
        sample_ys = np.clip(edge_ys - depth, 0, h - 1)
        accum += img[sample_ys, valid_cols].astype(np.float32)
    edge_colors[valid_cols] = accum / 6.0

    # --- Fill rows below the edge ---
    result = img.copy()
    bg = np.array(bg_color_rgb, dtype=np.float32)

    start_y = max(1, median_edge - 2)
    for y in range(start_y, h):
        needs_fill = (y > bottom_edge) & has_subject
        if not np.any(needs_fill):
            continue

        cols = np.where(needs_fill)[0]
        ey = bottom_edge[cols].astype(np.float32)
        t = np.clip((y - ey) / (h - ey), 0, 1)
        blend = np.clip(t ** 1.8, 0, 1).reshape(-1, 1)
        darken = (1.0 - t * 0.02).reshape(-1, 1)

        colors = edge_colors[cols] * darken * (1 - blend) + bg * blend
        result[y, cols] = np.clip(colors, 0, 255).astype(np.uint8)

    # --- Smooth the seam with inpainting ---
    seam_mask = np.zeros((h, w), dtype=np.uint8)
    ey_valid = bottom_edge[valid_cols]
    for dy in range(-1, 5):
        ys = np.clip(ey_valid + dy, 0, h - 1)
        seam_mask[ys, valid_cols] = 255

    if np.any(seam_mask):
        result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        result_bgr = cv2.inpaint(result_bgr, seam_mask, 5, cv2.INPAINT_TELEA)
        result = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)

    return Image.fromarray(result)


def extend_sides(
    pil_image: Image.Image,
    bg_color_rgb: tuple,
    body_start_y: int,
    bg_tolerance: int = 12,
) -> Image.Image:
    """Fill the body region below the chin so no background remains there.

    Every background-coloured pixel below ``body_start_y`` (the chin
    line) is inpainted from the surrounding body pixels.  This fills
    both the lateral margins beside the shoulders and any vertical gap
    between the bottom of the subject and the bottom of the frame, so
    the lower portion of the frame is fully covered by shoulders/body
    content per spec.  The head/neck above ``body_start_y`` is left
    untouched, preserving the clean background required around the
    head.

    Args:
        pil_image:    Composited RGB passport photo (PIL Image).
        bg_color_rgb: (R, G, B) background colour tuple.
        body_start_y: Pixel Y of the chin line.  Background pixels at
                      or below this row are filled; rows above are
                      preserved.  Computed by the caller from the spec
                      geometry (crown position + head height).
        bg_tolerance: Per-channel deviation under which a pixel counts
                      as background.

    Returns:
        PIL Image with the body region filled.  DPI metadata is
        preserved.  Returns the input unchanged when no fill is needed.
    """
    w, h = pil_image.size
    body_start_y = max(0, min(body_start_y, h - 1))
    if body_start_y >= h - 1:
        return pil_image

    img = np.array(pil_image)
    bg = np.array(bg_color_rgb, dtype=np.int16)
    diff = np.max(np.abs(img.astype(np.int16) - bg), axis=2)
    is_bg = diff <= bg_tolerance

    mask = np.zeros((h, w), dtype=np.uint8)
    mask[body_start_y:] = is_bg[body_start_y:].astype(np.uint8) * 255

    if not np.any(mask):
        return pil_image

    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)

    out = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))
    if "dpi" in pil_image.info:
        out.info["dpi"] = pil_image.info["dpi"]
    return out
