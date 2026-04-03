"""Background removal and replacement using rembg and Pillow.

Uses ISNet model with alpha matting for clean edges, plus post-processing
to preserve ears, blend hair naturally, and produce passport-quality results.

Hair matting strategy:
- Body/face/clothing edges → snapped to binary (sharp, no fringe)
- Hair zone → guided filter + gentle feathering (natural soft blending)
- Ear regions → skin-tone recovery (never clipped)
"""

from PIL import Image, ImageFilter
from rembg import remove, new_session
import numpy as np
import cv2
import io

# Use ISNet for better edge quality on portraits
_session = None


def _get_session():
    """Lazy-load the ISNet model session (downloaded on first use)."""
    global _session
    if _session is None:
        _session = new_session("isnet-general-use")
    return _session


def _guided_filter(guide, src, radius, eps):
    """Edge-preserving guided filter for alpha matting refinement.

    The guided filter smooths the alpha matte while preserving edges
    that exist in the guide (original) image. This produces natural
    hair-background transitions.

    Args:
        guide: Grayscale guide image (uint8)
        src: Source alpha (float32, 0-1)
        radius: Filter radius
        eps: Regularization (smaller = sharper edges)

    Returns:
        Filtered alpha (float32, 0-1)
    """
    guide = guide.astype(np.float32) / 255.0
    ksize = 2 * radius + 1

    mean_g = cv2.boxFilter(guide, -1, (ksize, ksize))
    mean_s = cv2.boxFilter(src, -1, (ksize, ksize))
    mean_gs = cv2.boxFilter(guide * src, -1, (ksize, ksize))
    mean_gg = cv2.boxFilter(guide * guide, -1, (ksize, ksize))

    cov_gs = mean_gs - mean_g * mean_s
    var_g = mean_gg - mean_g * mean_g

    a = cov_gs / (var_g + eps)
    b = mean_s - a * mean_g

    mean_a = cv2.boxFilter(a, -1, (ksize, ksize))
    mean_b = cv2.boxFilter(b, -1, (ksize, ksize))

    return mean_a * guide + mean_b


def remove_background(image_bytes):
    """Remove the background from a portrait photo.

    Uses ISNet model with alpha matting for natural hair edges,
    then refines the mask to preserve ears and sharpen subject edges.

    Args:
        image_bytes: Raw image bytes (JPEG/PNG)

    Returns:
        PIL Image in RGBA mode with transparent background
    """
    session = _get_session()

    # Run rembg with alpha matting — tighter thresholds for crisp edges
    result_bytes = remove(
        image_bytes,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=5,
        post_process_mask=False,  # skip built-in smoothing to keep edges sharp
    )
    rgba = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    # Refine: recover ears, sharpen body edges, soften only hair
    rgba = _refine_mask(rgba, image_bytes)

    return rgba


def _refine_mask(rgba_image, original_bytes):
    """Refine the alpha mask: sharp body/face edges, soft hair, preserved ears.

    Strategy:
    - Detect face to locate ear and hair regions
    - Recover clipped ears via skin-tone detection
    - Sharpen alpha edges on body/clothing/face (threshold snap)
    - Feather only the hair zone for natural blending
    """
    arr = np.array(rgba_image)
    alpha = arr[:, :, 3].copy()
    h, w = alpha.shape

    # Load original for face-aware refinement
    original = cv2.imdecode(
        np.frombuffer(original_bytes, np.uint8), cv2.IMREAD_COLOR
    )
    if original is None:
        return rgba_image

    # --- Detect face ---
    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

    # Default hair zone: top 20% of the foreground bounding box
    hair_zone = np.zeros((h, w), dtype=bool)

    if len(faces) > 0:
        fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])

        # --- Ear recovery via skin-tone detection ---
        ear_margin = int(fw * 0.25)
        ear_top = fy + int(fh * 0.1)
        ear_bottom = fy + int(fh * 0.7)

        left_x1 = max(0, fx - ear_margin)
        left_x2 = fx + int(fw * 0.15)
        right_x1 = fx + int(fw * 0.85)
        right_x2 = min(w, fx + fw + ear_margin)

        hsv = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([35, 255, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

        for x1, x2 in [(left_x1, left_x2), (right_x1, right_x2)]:
            region_mask = np.zeros_like(alpha)
            region_mask[ear_top:ear_bottom, x1:x2] = 1
            recovery = (skin_mask > 0) & (region_mask > 0) & (alpha < 128)
            alpha[recovery] = 240  # high confidence for skin pixels

        # --- Define hair zone: above the face top, full width of subject ---
        # Hair sits above the detected face, extending to the top of the subject
        hair_top = 0
        hair_bottom = fy + int(fh * 0.05)  # just above forehead
        # Horizontal bounds: slightly wider than face
        hair_left = max(0, fx - int(fw * 0.3))
        hair_right = min(w, fx + fw + int(fw * 0.3))
        hair_zone[hair_top:hair_bottom, hair_left:hair_right] = True
    else:
        # No face found — assume hair is in top 25% of foreground
        fg_rows = np.where(alpha > 128)[0]
        if len(fg_rows) > 0:
            fg_top = fg_rows.min()
            fg_height = fg_rows.max() - fg_top
            hair_zone[fg_top:fg_top + int(fg_height * 0.25), :] = True

    # --- Sharpen body/face edges (non-hair areas) ---
    # Snap semi-transparent pixels to solid: removes fuzzy fringing
    # on shoulders, clothing, jawline, etc.
    body_zone = ~hair_zone
    # Pixels in body zone with alpha between 20-235 → snap to 0 or 255
    semi_transparent_body = body_zone & (alpha > 20) & (alpha < 235)
    alpha[semi_transparent_body & (alpha >= 128)] = 255
    alpha[semi_transparent_body & (alpha < 128)] = 0

    # Clean up stray pixels on body edges with morphological close
    body_alpha = alpha.copy()
    body_alpha[hair_zone] = 0  # isolate body
    body_binary = (body_alpha > 128).astype(np.uint8) * 255
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    body_closed = cv2.morphologyEx(body_binary, cv2.MORPH_CLOSE, close_kernel)
    # Apply only where body zone and previously semi-transparent
    body_fix = body_zone & (body_closed > 0) & (alpha == 0)
    alpha[body_fix] = 255

    # --- Feather hair zone with guided filter for natural blending ---
    original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

    # Recover thin hair strands in the hair zone
    hy_coords, hx_coords = np.where(hair_zone)
    if len(hy_coords) > 0:
        hy_min, hy_max = hy_coords.min(), hy_coords.max() + 1
        hx_min, hx_max = hx_coords.min(), hx_coords.max() + 1
        hair_patch = alpha[hy_min:hy_max, hx_min:hx_max].copy()

        hair_orig = original_gray[hy_min:hy_max, hx_min:hx_max]
        bg_est = cv2.GaussianBlur(hair_orig, (31, 31), 0)
        diff = np.abs(hair_orig.astype(float) - bg_est.astype(float))

        # Recover pixels that differ from background but have low alpha
        strand_recovery = (hair_patch < 80) & (diff > 20)
        hair_patch[strand_recovery] = np.clip(
            (diff[strand_recovery] * 2.5).astype(np.uint8), 40, 180
        )
        alpha[hy_min:hy_max, hx_min:hx_max] = hair_patch

    # Apply guided filter ONLY to the transition band in the hair zone.
    # Pixels that are fully opaque or fully transparent stay as-is;
    # only the semi-transparent fringe (hair edges) gets smoothed.
    hair_transition = hair_zone & (alpha > 15) & (alpha < 240)

    if np.any(hair_transition):
        alpha_f = alpha.astype(np.float32) / 255.0
        guided = _guided_filter(original_gray, alpha_f, radius=4, eps=1e-2)
        guided = np.clip(guided * 255, 0, 255).astype(np.uint8)
        alpha[hair_transition] = guided[hair_transition]

    # Snap residual near-zero and near-full pixels in hair zone
    alpha[hair_zone & (alpha < 20)] = 0
    alpha[hair_zone & (alpha > 235)] = 255

    # --- Final cleanup: remove isolated small blobs in background ---
    binary_full = (alpha > 30).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary_full, connectivity=8
    )
    # Remove tiny disconnected fragments (noise)
    min_area = int(h * w * 0.001)  # 0.1% of image area
    for label_id in range(1, num_labels):
        if stats[label_id, cv2.CC_STAT_AREA] < min_area:
            alpha[labels == label_id] = 0

    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")


def replace_background(rgba_image, bg_color_rgb):
    """Composite an RGBA image onto a solid color background with edge blending.

    Args:
        rgba_image: PIL Image in RGBA mode (transparent background)
        bg_color_rgb: Tuple (R, G, B) for the target background color

    Returns:
        PIL Image in RGB mode with the solid background applied
    """
    # Ensure clean compositing
    background = Image.new("RGBA", rgba_image.size, bg_color_rgb + (255,))
    composite = Image.alpha_composite(background, rgba_image)
    return composite.convert("RGB")
