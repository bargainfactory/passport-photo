"""Content-aware fill via OpenCV inpainting.

Uses cv2.inpaint with the Telea (Fast Marching) algorithm — samples
surrounding pixels to reconstruct the masked region. Works well for
removing small objects, stray strands, and blemishes against locally
consistent backgrounds.
"""

from __future__ import annotations
import cv2
import numpy as np


def inpaint_region(image_bgr: np.ndarray, mask: np.ndarray, radius: int = 5) -> np.ndarray:
    """Fill the white regions of `mask` in `image_bgr` using surrounding context.

    Args:
        image_bgr: BGR image as uint8 numpy array.
        mask: Single-channel uint8 mask. Non-zero pixels are filled.
        radius: Neighborhood radius for the inpainting algorithm.
                Larger = smoother fills, slower.

    Returns:
        BGR image with the mask region reconstructed.
    """
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("image_bgr must be HxWx3 BGR")
    if mask.ndim != 2:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY) if mask.ndim == 3 else mask
    if mask.shape[:2] != image_bgr.shape[:2]:
        mask = cv2.resize(mask, (image_bgr.shape[1], image_bgr.shape[0]),
                          interpolation=cv2.INTER_NEAREST)
    # Binarize the mask so partial-alpha brush strokes count
    binary_mask = (mask > 8).astype(np.uint8) * 255
    if not binary_mask.any():
        return image_bgr
    # Dilate slightly so edges blend rather than leaving seams
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary_mask = cv2.dilate(binary_mask, kernel, iterations=1)
    return cv2.inpaint(image_bgr, binary_mask, radius, cv2.INPAINT_TELEA)
