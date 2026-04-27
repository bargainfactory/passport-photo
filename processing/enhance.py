"""Photo enhancement: lighting correction, skin-tone retouching, print sharpening.

Takes a casual selfie and transforms it into studio-quality output through:
1. Adaptive lighting correction (CLAHE on luminance)
2. Face-aware shadow removal
3. Skin-tone aware white balance
4. Subtle skin smoothing (bilateral, texture-preserving)
5. Natural contrast enhancement
6. Print-ready unsharp mask sharpening
"""

import cv2
import numpy as np
from PIL import Image


def correct_lighting(bgr_image, face_rect=None):
    """Correct uneven lighting using adaptive histogram equalization.

    Applies CLAHE to the luminance channel in LAB color space so colors
    stay faithful while brightness is evened out.

    Args:
        bgr_image: OpenCV BGR numpy array
        face_rect: Optional (x, y, w, h) — unused here but kept for API consistency

    Returns:
        Lighting-corrected BGR image
    """
    lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Gentle CLAHE: lower clip limit avoids over-enhancement and keeps
    # skin-tone gradients natural. Higher tile grid = finer local adapt
    # without posterizing the skin.
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
    l_corrected = clahe.apply(l)

    # 25% corrected / 75% original — CLAHE lifts midtones which, combined
    # with downstream contrast + sharpen, was producing an over-exposed
    # look. This ratio corrects uneven lighting without raising the
    # overall brightness.
    l_blended = cv2.addWeighted(l_corrected, 0.25, l, 0.75, 0)

    return cv2.cvtColor(cv2.merge([l_blended, a, b]), cv2.COLOR_LAB2BGR)


def remove_shadows(bgr_image, face_rect):
    """Remove harsh shadows from the face and upper body region.

    Estimates a smooth illumination map and divides it out, then
    re-scales so mean brightness is preserved.

    Args:
        bgr_image: OpenCV BGR numpy array
        face_rect: (x, y, w, h) face bounding box

    Returns:
        Shadow-corrected BGR image
    """
    if face_rect is None:
        return bgr_image

    x, y, w, h = face_rect
    result = bgr_image.copy()

    # Work on a generous region around the face (includes neck/shoulders)
    margin_x = int(w * 0.4)
    margin_top = int(h * 0.3)
    margin_bot = int(h * 0.6)
    y1 = max(0, y - margin_top)
    y2 = min(bgr_image.shape[0], y + h + margin_bot)
    x1 = max(0, x - margin_x)
    x2 = min(bgr_image.shape[1], x + w + margin_x)

    region = bgr_image[y1:y2, x1:x2].copy()
    if region.size == 0:
        return bgr_image

    # Convert to LAB for luminance manipulation
    region_lab = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
    l_ch = region_lab[:, :, 0].astype(np.float32)

    # Estimate illumination with a large-sigma Gaussian
    sigma = max(w // 3, 15)
    ksize = int(sigma * 4) | 1  # ensure odd
    illumination = cv2.GaussianBlur(l_ch, (ksize, ksize), sigma)

    # Normalize: divide by illumination, scale to preserve mean
    mean_l = np.mean(l_ch)
    safe_illum = np.clip(illumination, 1.0, 255.0)
    corrected = l_ch * (mean_l / safe_illum)
    corrected = np.clip(corrected, 0, 255).astype(np.uint8)

    # 40% corrected / 60% original — removes harsh shadows without
    # flattening the natural luminance falloff on the face, which is
    # what preserves a lifelike skin tone.
    region_lab[:, :, 0] = cv2.addWeighted(corrected, 0.40, region_lab[:, :, 0], 0.60, 0)
    result[y1:y2, x1:x2] = cv2.cvtColor(region_lab, cv2.COLOR_LAB2BGR)

    return result


def white_balance_skin_aware(bgr_image, face_rect):
    """Neutralize color casts while preserving natural skin warmth.

    Works in LAB space (perceptually uniform) so corrections are linear
    in perceived color. Measures the sampled forehead's a* / b* values
    against a realistic skin target and pulls deviations partway back.

    The prior RGB-ratio implementation tended to push cool-ish skin
    toward an overly warm target, producing a yellow cast. LAB space
    with a tight deadzone avoids that failure mode.

    Args:
        bgr_image: OpenCV BGR numpy array
        face_rect: (x, y, w, h) face bounding box

    Returns:
        White-balanced BGR image (often unchanged)
    """
    if face_rect is None:
        return bgr_image  # no reliable reference — skip WB

    x, y, w, h = face_rect

    # Sample from forehead (most uniform skin region)
    cx, cy = x + w // 2, y + int(h * 0.30)
    s = max(w // 10, 6)
    sy1 = max(0, cy - s); sy2 = min(bgr_image.shape[0], cy + s)
    sx1 = max(0, cx - s); sx2 = min(bgr_image.shape[1], cx + s)
    sample = bgr_image[sy1:sy2, sx1:sx2]
    if sample.size == 0:
        return bgr_image

    # OpenCV LAB: 128 = neutral on a* and b*. Healthy skin lives at
    # roughly a* ~ 138 (slight red) and b* ~ 143 (slight yellow —
    # natural warmth but not a cast). Values well above these targets
    # read as yellow / orange and must be pulled back.
    TARGET_A = 138.0
    TARGET_B = 143.0
    DEADZONE = 6.0      # LAB units — tolerate small natural variation
    STRENGTH = 0.6      # fraction of the deviation to remove

    sample_lab = cv2.cvtColor(sample, cv2.COLOR_BGR2LAB)
    avg_a = float(np.mean(sample_lab[:, :, 1]))
    avg_b = float(np.mean(sample_lab[:, :, 2]))

    shift_a = avg_a - TARGET_A
    shift_b = avg_b - TARGET_B

    if abs(shift_a) < DEADZONE and abs(shift_b) < DEADZONE:
        return bgr_image  # within natural skin range — no cast to fix

    lab_full = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab_full[:, :, 1] -= shift_a * STRENGTH
    lab_full[:, :, 2] -= shift_b * STRENGTH
    lab_full = np.clip(lab_full, 0, 255).astype(np.uint8)
    return cv2.cvtColor(lab_full, cv2.COLOR_LAB2BGR)


def _gray_world_wb(bgr_image):
    """Fallback gray-world white balance when no face is detected."""
    result = bgr_image.astype(np.float32)
    avgs = [float(np.mean(result[:, :, c])) for c in range(3)]
    avg_all = sum(avgs) / 3.0
    for c in range(3):
        if avgs[c] > 0:
            result[:, :, c] *= avg_all / avgs[c]
    return np.clip(result, 0, 255).astype(np.uint8)


def smooth_skin(bgr_image, face_rect):
    """Light airbrush — even out skin tone while keeping moles and scars.

    Uses an edge-preserving bilateral filter at parameters tuned to
    smooth low-frequency skin tone variation (blotches, redness, fine
    lines) while leaving high-contrast features (moles, scars,
    eyebrows, eye details) intact. Two passes give a soft airbrush
    finish without the plastic look of single heavy smoothing.

    Args:
        bgr_image: OpenCV BGR numpy array
        face_rect: (x, y, w, h) face bounding box

    Returns:
        Skin-smoothed BGR image
    """
    if face_rect is None:
        return bgr_image

    x, y, w, h = face_rect
    result = bgr_image.copy()

    # Generous region — face + neck + forehead so the airbrush carries
    # naturally through the chin/jaw line into the neck.
    margin_x = int(w * 0.30)
    margin_top = int(h * 0.30)
    margin_bot = int(h * 0.55)
    y1 = max(0, y - margin_top)
    y2 = min(bgr_image.shape[0], y + h + margin_bot)
    x1 = max(0, x - margin_x)
    x2 = min(bgr_image.shape[1], x + w + margin_x)

    face = bgr_image[y1:y2, x1:x2]
    if face.size == 0:
        return bgr_image

    # Two-pass bilateral. sigmaColor=38 sits above typical skin tone
    # noise (~10-25 LAB units) but well below the contrast of moles,
    # scars, eyebrows, lashes — those features have ΔL > 50 and survive.
    smoothed = cv2.bilateralFilter(face, d=9, sigmaColor=38, sigmaSpace=18)
    smoothed = cv2.bilateralFilter(smoothed, d=9, sigmaColor=38, sigmaSpace=18)

    # Skin-tone detection (slightly broader range to catch tanned + neck).
    hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
    skin_mask = cv2.inRange(
        hsv,
        np.array([0, 18, 55], dtype=np.uint8),
        np.array([35, 255, 255], dtype=np.uint8),
    )
    skin_mask = cv2.dilate(skin_mask, np.ones((5, 5), np.uint8), iterations=1)
    # Soft-edge mask so the smoothed region blends naturally into the
    # surrounding skin without a visible boundary.
    skin_mask = cv2.GaussianBlur(skin_mask, (21, 21), 0).astype(np.float32) / 255.0
    skin_mask_3ch = np.stack([skin_mask] * 3, axis=-1)

    # 60% airbrush / 40% original on skin — visible smoothing without
    # erasing pores entirely. Bilateral keeps moles + scars sharp at
    # this strength because their ΔL exceeds sigmaColor.
    blend = skin_mask_3ch * 0.60
    blended = (
        smoothed.astype(np.float32) * blend
        + face.astype(np.float32) * (1.0 - blend)
    ).clip(0, 255).astype(np.uint8)

    result[y1:y2, x1:x2] = blended
    return result


def enhance_contrast(bgr_image):
    """Gentle contrast boost for a professional look.

    Applies a mild S-curve via look-up table to the luminance channel.

    Args:
        bgr_image: OpenCV BGR numpy array

    Returns:
        Contrast-enhanced BGR image
    """
    lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Very gentle S-curve — aggressive contrast darkens midtone skin
    # and lightens highlights in an unflattering way. 0.08 boost is
    # enough to add presence without distorting skin tonality.
    lut = np.arange(256, dtype=np.float32)
    lut = lut / 255.0
    lut = 0.5 + (lut - 0.5) * (1.0 + 0.08 * (2 * np.abs(lut - 0.5)))
    lut = np.clip(lut * 255, 0, 255).astype(np.uint8)

    l_enhanced = cv2.LUT(l, lut)
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)


def sharpen_for_print(bgr_image):
    """Unsharp mask tuned for 300 DPI passport photo printing.

    Sharpens fine details (eyes, hair texture, fabric) without
    amplifying noise or creating halos.

    Args:
        bgr_image: OpenCV BGR numpy array

    Returns:
        Print-sharpened BGR image
    """
    # Two-pass unsharp mask: fine detail + medium structure
    # Pass 1: fine details (eyes, hair texture, skin pores)
    blur_fine = cv2.GaussianBlur(bgr_image, (0, 0), sigmaX=1.0)
    sharp1 = cv2.addWeighted(bgr_image, 1.5, blur_fine, -0.5, 0)
    sharp1 = np.clip(sharp1, 0, 255).astype(np.uint8)

    # Pass 2: medium structure (facial features, clothing edges)
    blur_med = cv2.GaussianBlur(sharp1, (0, 0), sigmaX=2.5)
    sharp2 = cv2.addWeighted(sharp1, 1.3, blur_med, -0.3, 0)
    return np.clip(sharp2, 0, 255).astype(np.uint8)


def full_enhance_pipeline(bgr_image, face_rect=None):
    """Run the complete enhancement pipeline.

    Args:
        bgr_image: OpenCV BGR numpy array (original or post-bg-replacement)
        face_rect: (x, y, w, h) or None

    Returns:
        Fully enhanced BGR image
    """
    img = correct_lighting(bgr_image, face_rect)
    img = remove_shadows(img, face_rect)
    img = white_balance_skin_aware(img, face_rect)
    img = smooth_skin(img, face_rect)
    img = enhance_contrast(img)
    img = sharpen_for_print(img)
    return img
