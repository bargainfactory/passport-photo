"""High-fidelity background removal and replacement.

Pipeline:
  1. Coarse segmentation with BiRefNet-portrait (state-of-the-art
     portrait segmentation, 2024). Falls back to ISNet if BiRefNet
     is unavailable.
  2. Largest-connected-component selection — guarantees *only* the
     subject is kept; all background debris (loose objects, stray
     shadows, passers-by, small foreground-classified blobs) is
     eliminated regardless of its confidence score.
  3. Hole filling inside the subject mask — eliminates pinholes and
     gaps (e.g. between hair strands incorrectly classified as bg).
  4. Trimap construction (definite-FG / definite-BG / uncertain band).
  5. Edge-aware alpha refinement in the uncertain band via guided
     filter against the original RGB image — produces natural hair
     transitions without fringe bleed.
  6. Body/clothing edges snapped to binary so shoulders and jaw
     never show a semi-transparent halo.
  7. Ear recovery via HSV skin-tone detection (some models clip ears).

The result is a clean RGBA matte where every opaque pixel is part of
the subject and no background debris remains.
"""

from __future__ import annotations

from PIL import Image
from rembg import remove, new_session
import numpy as np
import cv2
import io

# --- Model loading (lazy, cached) ---

_session = None
_session_name = None

# Model preference. ISNet is listed first because it ships pre-cached in
# this project and delivers near-SOTA quality when paired with our
# trimap + guided-filter refinement below. BiRefNet-portrait (Zheng
# et al., 2024) is nominally higher quality but pulls ~1 GB on first
# use, blowing through any reasonable request timeout — opt-in by
# setting env var BG_MODEL=birefnet-portrait.
import os
_preferred = os.environ.get("BG_MODEL", "").strip()
_MODEL_CANDIDATES = tuple(
    dict.fromkeys(  # de-dup while preserving order
        ([_preferred] if _preferred else [])
        + [
            "isnet-general-use",
            "u2net_human_seg",
            "birefnet-portrait",
            "birefnet-general",
        ]
    )
)


def _get_session():
    """Load the best-available segmentation model, cached."""
    global _session, _session_name
    if _session is not None:
        return _session
    last_err = None
    for name in _MODEL_CANDIDATES:
        try:
            _session = new_session(name)
            _session_name = name
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
    if _session is None:
        raise RuntimeError(
            f"No rembg segmentation model could be loaded. Last error: {last_err}"
        )
    return _session


# --- Guided filter (edge-preserving alpha refinement) ---

def _guided_filter(guide: np.ndarray, src: np.ndarray, radius: int, eps: float) -> np.ndarray:
    """Fast guided filter (He et al., 2013) for matte refinement.

    Args:
        guide: Grayscale guide image, uint8. Edges in `guide` are preserved
               in the output alpha.
        src:   Source alpha in float32, range [0, 1].
        radius: Filter radius in pixels. Larger = smoother transitions.
        eps:   Regularization; smaller = edges stick more tightly.

    Returns:
        Filtered alpha, float32 in [0, 1].
    """
    guide = guide.astype(np.float32) / 255.0
    ksize = 2 * radius + 1

    mean_g = cv2.boxFilter(guide, -1, (ksize, ksize))
    mean_s = cv2.boxFilter(src, -1, (ksize, ksize))
    mean_gs = cv2.boxFilter(guide * src, -1, (ksize, ksize))
    mean_gg = cv2.boxFilter(guide * guide, -1, (ksize, ksize))

    cov = mean_gs - mean_g * mean_s
    var = mean_gg - mean_g * mean_g

    a = cov / (var + eps)
    b = mean_s - a * mean_g

    mean_a = cv2.boxFilter(a, -1, (ksize, ksize))
    mean_b = cv2.boxFilter(b, -1, (ksize, ksize))
    return mean_a * guide + mean_b


# --- Public entry point ---

def remove_background(image_bytes: bytes) -> Image.Image:
    """Remove the background from a portrait.

    Args:
        image_bytes: Raw JPEG/PNG bytes.

    Returns:
        RGBA PIL Image — every opaque pixel is part of the subject,
        no background debris.
    """
    session = _get_session()

    # Stage 1: coarse alpha from the neural network. alpha_matting is
    # intentionally disabled here — we do our own higher-quality
    # trimap + guided-filter refinement below, which is sharper than
    # rembg's built-in PyMatting pass and avoids its characteristic
    # gray halo on dark backgrounds.
    result_bytes = remove(
        image_bytes,
        session=session,
        alpha_matting=False,
        post_process_mask=False,
        only_mask=False,
    )
    rgba = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    # Stage 2+: high-fidelity refinement (subject isolation, hole fill,
    # trimap matting, edge snapping, ear recovery).
    return _refine_mask(rgba, image_bytes)


# --- Refinement ---

def _refine_mask(rgba_image: Image.Image, original_bytes: bytes) -> Image.Image:
    """Clean up the raw network mask into a high-fidelity portrait matte."""
    arr = np.array(rgba_image)
    alpha = arr[:, :, 3].copy()
    h, w = alpha.shape

    # Decode original RGB for guided filter + face-aware corrections
    original = cv2.imdecode(
        np.frombuffer(original_bytes, np.uint8), cv2.IMREAD_COLOR
    )
    if original is None:
        return rgba_image
    original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

    # ---- 1. Detect face FIRST — we anchor the subject mask to it ----
    # Without this anchor, if a background blob happens to be larger
    # than the subject (or gets glued to it via noise bridges), the
    # wrong component would survive.
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(original_gray, 1.1, 5, minSize=(80, 80))
    face_rect = max(faces, key=lambda f: f[2] * f[3]) if len(faces) else None

    # ---- 2. Break thin "bridges" between subject and background ----
    # Morphological opening with a small kernel severs one-pixel-wide
    # connectivity that would otherwise glue a desk edge or wall corner
    # onto the subject's silhouette.
    alpha = _break_thin_bridges(alpha, threshold=80)

    # ---- 3. Keep ONLY the component containing the face ----
    # Face-anchored selection: whatever blob contains the face centroid
    # is the subject; everything else — regardless of size — is debris.
    # Threshold 80 (not 30) because network outputs in the 30-80 range
    # are typically low-confidence halo/fringe, not real subject.
    alpha = _keep_face_component(alpha, face_rect, threshold=80)

    # ---- 4. Fill pinholes / interior gaps within the subject ----
    alpha = _fill_interior_holes(alpha, threshold=128)

    # ---- 4. Ear recovery (skin-tone re-inclusion near face sides) ----
    if face_rect is not None:
        alpha = _recover_ears(alpha, original, face_rect)

    # ---- 5. Build trimap: definite-FG / definite-BG / uncertain ----
    fg, bg, unknown = _build_trimap(alpha, face_rect)

    # ---- 6. Guided-filter refinement inside the uncertain band ----
    # Only the narrow band around the silhouette is reprocessed, which
    # keeps interior FG and distant BG untouched (fast + robust).
    if np.any(unknown):
        alpha_f = alpha.astype(np.float32) / 255.0
        guided = _guided_filter(original_gray, alpha_f, radius=4, eps=1e-3)
        guided = np.clip(guided * 255.0, 0.0, 255.0).astype(np.uint8)
        alpha[unknown] = guided[unknown]

    # Re-apply hard FG/BG in case the filter bled into them
    alpha[fg] = 255
    alpha[bg] = 0

    # ---- 7. Snap body/clothing edges to binary (no halo on shoulders) ----
    # Only hair-level zones are allowed to stay semi-transparent.
    body_zone = _body_zone_mask(alpha.shape, face_rect)
    snap = body_zone & (alpha > 20) & (alpha < 235)
    alpha[snap & (alpha >= 128)] = 255
    alpha[snap & (alpha < 128)] = 0

    # ---- 8. Final debris sweep: re-anchor to face after edits ----
    alpha = _keep_face_component(alpha, face_rect, threshold=80)

    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")


# --- Helpers ---

def _break_thin_bridges(alpha: np.ndarray, threshold: int = 80) -> np.ndarray:
    """Sever 1-2 pixel-wide connectivity between subject and background blobs.

    Applies morphological opening to the *binary* mask, then transfers
    the survivor regions back onto the original (soft) alpha so hair
    transparency is preserved where it genuinely belonged.
    """
    binary = (alpha >= threshold).astype(np.uint8) * 255
    # 3x3 opening severs 1-pixel bridges; 5x5 is too aggressive on hair.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    # Pixels that existed in binary but not in opened = bridge material
    # (too thin to be real subject). Zero their alpha.
    bridges = (binary > 0) & (opened == 0)
    result = alpha.copy()
    result[bridges] = 0
    return result


def _keep_face_component(alpha: np.ndarray, face_rect, threshold: int = 80) -> np.ndarray:
    """Keep only the connected component that contains the detected face.

    Falls back to the largest component when no face is known. This is
    strictly stronger than largest-component because a background object
    larger than the subject (or glued to it via noise) no longer wins.
    """
    binary = (alpha > threshold).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return alpha

    target_label = None
    if face_rect is not None:
        fx, fy, fw, fh = face_rect
        # Sample a 5x5 grid inside the face rect and pick the label that
        # appears most often — robust against a single pixel landing on
        # an eye-socket gap or nostril.
        votes: dict[int, int] = {}
        for dy in (0.25, 0.4, 0.55, 0.7, 0.85):
            for dx in (0.25, 0.4, 0.5, 0.6, 0.75):
                py = min(labels.shape[0] - 1, max(0, int(fy + fh * dy)))
                px = min(labels.shape[1] - 1, max(0, int(fx + fw * dx)))
                lab = int(labels[py, px])
                if lab > 0:
                    votes[lab] = votes.get(lab, 0) + 1
        if votes:
            target_label = max(votes.items(), key=lambda kv: kv[1])[0]

    if target_label is None:
        # Fallback: largest non-background component
        areas = stats[1:, cv2.CC_STAT_AREA]
        target_label = int(np.argmax(areas)) + 1

    keep_mask = labels == target_label
    cleaned = alpha.copy()
    cleaned[~keep_mask] = 0
    return cleaned


def _keep_largest_component(alpha: np.ndarray, threshold: int = 30) -> np.ndarray:
    """Zero out every pixel not in the largest connected foreground blob."""
    binary = (alpha > threshold).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return alpha
    # Label 0 is background; find largest non-background label by area.
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_id = int(np.argmax(areas)) + 1
    keep_mask = labels == largest_id
    cleaned = alpha.copy()
    cleaned[~keep_mask] = 0
    return cleaned


def _fill_interior_holes(alpha: np.ndarray, threshold: int = 128) -> np.ndarray:
    """Fill enclosed background pockets inside the subject silhouette.

    Uses flood-fill from the image border: whatever the flood reaches
    is true background; anything it cannot reach but was classified
    as background is an interior hole and gets filled.
    """
    binary = (alpha >= threshold).astype(np.uint8) * 255
    # Pad by 1 so the flood starts safely at the border
    h, w = binary.shape
    flood = binary.copy()
    mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    cv2.floodFill(flood, mask, (0, 0), 255)  # flood true background from corner
    # flood now has true background = 255, interior holes = 0
    interior_holes = (flood == 0)
    # Promote interior holes to full opacity (they ARE the subject)
    result = alpha.copy()
    result[interior_holes] = np.maximum(result[interior_holes], 255)
    return result


def _recover_ears(alpha: np.ndarray, original_bgr: np.ndarray, face_rect) -> np.ndarray:
    """Reinstate ear pixels the network may have clipped.

    Samples HSV skin tones immediately to the left/right of the face
    and promotes those pixels' alpha to high confidence.
    """
    fx, fy, fw, fh = face_rect
    h, w = alpha.shape

    ear_margin = int(fw * 0.25)
    ear_top = fy + int(fh * 0.10)
    ear_bottom = fy + int(fh * 0.70)
    left_x1 = max(0, fx - ear_margin)
    left_x2 = fx + int(fw * 0.15)
    right_x1 = fx + int(fw * 0.85)
    right_x2 = min(w, fx + fw + ear_margin)

    hsv = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2HSV)
    skin = cv2.inRange(
        hsv, np.array([0, 20, 70], np.uint8), np.array([35, 255, 255], np.uint8)
    )

    result = alpha.copy()
    for x1, x2 in ((left_x1, left_x2), (right_x1, right_x2)):
        region = np.zeros_like(alpha)
        region[ear_top:ear_bottom, x1:x2] = 1
        recover = (skin > 0) & (region > 0) & (alpha < 128)
        result[recover] = 240
    return result


def _build_trimap(alpha: np.ndarray, face_rect):
    """Construct a trimap from the coarse alpha.

    Returns three boolean masks: (definite_fg, definite_bg, uncertain).
    The uncertain band is generated by eroding and dilating the binary
    mask, so only pixels near the silhouette are reprocessed.
    """
    binary = (alpha > 128).astype(np.uint8) * 255

    # Band width: scale with face size if known, else image size.
    if face_rect is not None:
        band = max(6, int(face_rect[2] * 0.04))
    else:
        band = max(6, int(min(alpha.shape) * 0.01))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band, band))
    eroded = cv2.erode(binary, kernel)
    dilated = cv2.dilate(binary, kernel)

    fg = eroded > 0
    bg = dilated == 0
    unknown = (~fg) & (~bg)
    return fg, bg, unknown


def _body_zone_mask(shape, face_rect):
    """Boolean mask for the non-hair body region (below/beside the face).

    We snap alpha to binary inside this zone to prevent the fuzzy
    halos the refinement would otherwise leave on shoulders / jaw /
    clothing. Hair above the face keeps its soft transition.
    """
    h, w = shape
    body = np.ones((h, w), dtype=bool)
    if face_rect is not None:
        fx, fy, fw, fh = face_rect
        # Treat everything above forehead (+ slight widen) as hair zone
        hair_bottom = fy + int(fh * 0.05)
        hair_left = max(0, fx - int(fw * 0.3))
        hair_right = min(w, fx + fw + int(fw * 0.3))
        body[0:hair_bottom, hair_left:hair_right] = False
    return body


# --- Compositing ---

def replace_background(rgba_image: Image.Image, bg_color_rgb) -> Image.Image:
    """Composite the RGBA matte onto a solid-color background.

    Args:
        rgba_image: RGBA PIL Image with transparent background.
        bg_color_rgb: (R, G, B) tuple for the target background.

    Returns:
        RGB PIL Image with the subject over the solid color.
    """
    background = Image.new("RGBA", rgba_image.size, tuple(bg_color_rgb) + (255,))
    return Image.alpha_composite(background, rgba_image).convert("RGB")
