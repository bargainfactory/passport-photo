"""Extend shoulders to fill the bottom gap in cropped passport photos.

After cropping to spec, the subject's body may not reach the bottom of
the frame, leaving background-colored space below the shoulders. This
module detects that gap and fills it by stretching the clothing colors
downward with a natural gradient, then smoothing the seam with
inpainting — the same principle as Photoshop's Content-Aware Fill.
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
