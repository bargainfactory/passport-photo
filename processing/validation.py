"""Photo validation checks for passport/visa compliance.

Runs a series of heuristic checks on the uploaded image and detected face
to flag potential issues before processing.
"""

import cv2
import numpy as np
from config.constants import MAX_TILT_DEGREES, MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT

# MediaPipe Face Mesh gives reliable landmark-based eye/mouth analysis
# across skin tones and lighting. Fall back to heuristics if unavailable.
_mp_face_mesh = None
_mp_available = False
try:
    import mediapipe as mp
    _mp_available = True
except ImportError:
    pass


def _get_face_mesh():
    """Lazy-load MediaPipe FaceMesh."""
    global _mp_face_mesh
    if _mp_face_mesh is None and _mp_available:
        _mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )
    return _mp_face_mesh


def _landmarks(image_bgr):
    """Return FaceMesh landmarks (normalized 0-1) or None."""
    mesh = _get_face_mesh()
    if mesh is None:
        return None
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    res = mesh.process(rgb)
    if not res.multi_face_landmarks:
        return None
    return res.multi_face_landmarks[0].landmark


def validate_photo(image_bgr, face_rect, face_metrics, spec=None):
    """Run all validation checks on an uploaded photo.

    Args:
        image_bgr: numpy array in BGR format
        face_rect: (x, y, w, h) or None
        face_metrics: dict from compute_face_metrics() or None
        spec: Optional country spec dict for spec-specific checks

    Returns:
        List of dicts: [{"check": str, "passed": bool, "message": str}, ...]
    """
    results = []
    h, w = image_bgr.shape[:2]

    # 1. Resolution check
    results.append({
        "check": "Resolution",
        "passed": w >= MIN_IMAGE_WIDTH and h >= MIN_IMAGE_HEIGHT,
        "message": (
            f"Image is {w}x{h}px. "
            + ("Sufficient resolution." if w >= MIN_IMAGE_WIDTH and h >= MIN_IMAGE_HEIGHT
               else f"Minimum {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}px recommended.")
        ),
    })

    # 2. Face detected
    face_found = face_rect is not None
    results.append({
        "check": "Face detected",
        "passed": face_found,
        "message": "Face detected successfully." if face_found else "No face detected. Please use a clear, front-facing photo.",
    })

    if not face_found or face_metrics is None:
        return results

    x, y, fw, fh = face_rect

    # 3. Single face (the detection already picks the largest, but warn if face is too small)
    face_area_pct = (fw * fh) / (w * h) * 100
    results.append({
        "check": "Face size",
        "passed": face_area_pct > 3,
        "message": (
            f"Face occupies {face_area_pct:.1f}% of image. "
            + ("Good." if face_area_pct > 3 else "Face is too small. Move closer to the camera.")
        ),
    })

    # 4. Face centered horizontally
    center_x = face_metrics["center_x"]
    offset_pct = abs(center_x - w / 2) / w * 100
    results.append({
        "check": "Centered",
        "passed": offset_pct < 10,
        "message": (
            f"Face is {offset_pct:.1f}% off-center. "
            + ("Well centered." if offset_pct < 10 else "Please center your face in the frame.")
        ),
    })

    # 5. Head tilt
    tilt = face_metrics.get("tilt_degrees", 0)
    results.append({
        "check": "Head tilt",
        "passed": bool(tilt < MAX_TILT_DEGREES),
        "message": (
            f"Head tilt: {tilt:.1f}\u00b0. "
            + ("Acceptable." if tilt < MAX_TILT_DEGREES
               else f"Tilt exceeds {MAX_TILT_DEGREES}\u00b0. Please straighten your head.")
        ),
    })

    # 6. Shadow detection (brightness variance in background regions)
    shadow_ok, shadow_msg = _check_shadows(image_bgr, face_rect)
    results.append({
        "check": "Shadows",
        "passed": shadow_ok,
        "message": shadow_msg,
    })

    # 7. Red-eye check (basic heuristic)
    redeye_ok = _check_red_eye(image_bgr, face_rect)
    results.append({
        "check": "Red-eye",
        "passed": redeye_ok,
        "message": "No red-eye detected." if redeye_ok else "Possible red-eye detected. Consider retaking without flash.",
    })

    # 8. Eyes open check
    eyes_open, eyes_msg = _check_eyes_open(image_bgr, face_rect)
    results.append({
        "check": "Eyes open",
        "passed": eyes_open,
        "message": eyes_msg,
    })

    # 9. Mouth closed (no teeth showing)
    mouth_closed, mouth_msg = _check_mouth_closed(image_bgr, face_rect)
    results.append({
        "check": "Mouth closed",
        "passed": mouth_closed,
        "message": mouth_msg,
    })

    return results


def _check_shadows(image_bgr, face_rect):
    """Check for uneven shadows by analyzing brightness in background regions.

    Compares brightness variance between left and right sides of the face area.
    """
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    x, y, fw, fh = face_rect

    # Sample background regions on left and right of face
    margin = max(20, int(fw * 0.3))
    left_region = gray[y:y + fh, max(0, x - margin):x]
    right_region = gray[y:y + fh, x + fw:min(w, x + fw + margin)]

    if left_region.size == 0 or right_region.size == 0:
        return True, "Unable to assess shadows (face near edge)."

    left_mean = np.mean(left_region)
    right_mean = np.mean(right_region)
    diff = abs(float(left_mean) - float(right_mean))

    if diff > 40:
        return False, f"Uneven lighting detected (brightness diff: {diff:.0f}). Ensure even, front-facing light."
    return True, "Lighting appears even."


def _check_red_eye(image_bgr, face_rect):
    """Basic red-eye detection by checking for high red channel in eye region."""
    x, y, fw, fh = face_rect

    # Approximate eye region: upper 40% of face, middle 80% width
    eye_top = y + int(fh * 0.2)
    eye_bottom = y + int(fh * 0.45)
    eye_left = x + int(fw * 0.1)
    eye_right = x + int(fw * 0.9)

    if eye_top >= eye_bottom or eye_left >= eye_right:
        return True

    eye_region = image_bgr[eye_top:eye_bottom, eye_left:eye_right]
    if eye_region.size == 0:
        return True

    b, g, r = cv2.split(eye_region)
    # Red-eye: high red, low green and blue
    red_mask = (r > 150) & (r > g * 1.5) & (r > b * 1.5)
    red_pct = np.sum(red_mask) / red_mask.size * 100

    return bool(red_pct < 2)  # Less than 2% red pixels = no red-eye


def _eye_aspect_ratio(landmarks, img_w, img_h, indices):
    """Compute Eye Aspect Ratio (EAR) from FaceMesh landmarks.

    indices = (outer, inner, top1, top2, bottom1, bottom2)
    EAR = (|top1-bottom1| + |top2-bottom2|) / (2 * |outer-inner|)
    Open eye ~0.25-0.35, closed eye <0.15.
    """
    pts = []
    for idx in indices:
        lm = landmarks[idx]
        pts.append(np.array([lm.x * img_w, lm.y * img_h]))
    outer, inner, t1, t2, b1, b2 = pts
    horiz = np.linalg.norm(outer - inner)
    if horiz < 1e-3:
        return 0.0
    vert = (np.linalg.norm(t1 - b1) + np.linalg.norm(t2 - b2)) / 2.0
    return float(vert / horiz)


def _check_eyes_open(image_bgr, face_rect):
    """Check if both eyes are open using Eye Aspect Ratio (EAR).

    Uses MediaPipe Face Mesh landmarks — robust across skin tones and
    lighting. Falls back to a lenient Haar check if FaceMesh fails.
    """
    h, w = image_bgr.shape[:2]
    landmarks = _landmarks(image_bgr)

    if landmarks is not None:
        # Right eye (subject's right): 33 outer, 133 inner, 159/158 top, 145/153 bottom
        # Left eye:                    263 outer, 362 inner, 386/385 top, 374/380 bottom
        try:
            ear_r = _eye_aspect_ratio(landmarks, w, h, (33, 133, 159, 158, 145, 153))
            ear_l = _eye_aspect_ratio(landmarks, w, h, (263, 362, 386, 385, 374, 380))
        except (IndexError, AttributeError):
            ear_r = ear_l = 0.25

        ear_avg = (ear_r + ear_l) / 2.0
        # 0.18 is a well-accepted closed-eye threshold in the drowsiness-
        # detection literature. Anything above that is considered open.
        if ear_avg >= 0.18:
            return True, "Both eyes appear open."
        # Only one eye clearly closed — warn
        if min(ear_r, ear_l) < 0.15 and max(ear_r, ear_l) >= 0.18:
            return False, "One eye may be partially closed. Keep both eyes fully open."
        return False, "Eyes may be closed. Keep both eyes open and clearly visible."

    # --- Fallback: lenient Haar check (benefit of the doubt) ---
    x, y, fw, fh = face_rect
    eye_region = image_bgr[y + int(fh * 0.18):y + int(fh * 0.45),
                           x + int(fw * 0.05):x + int(fw * 0.95)]
    if eye_region.size == 0:
        return True, "Both eyes appear open."
    gray_eyes = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    eyes = eye_cascade.detectMultiScale(gray_eyes, 1.1, 3)
    if len(eyes) >= 1:
        return True, "Both eyes appear open."
    # Only fail if eye-tree-eyeglasses cascade also finds nothing
    alt = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
    if len(alt.detectMultiScale(gray_eyes, 1.1, 3)) >= 1:
        return True, "Both eyes appear open."
    return False, "Eyes may be closed. Keep both eyes open and clearly visible."


def _mouth_aspect_ratio(landmarks, img_w, img_h):
    """Mouth Aspect Ratio — vertical lip gap / horizontal mouth width.

    Uses inner lip landmarks (13 upper, 14 lower) and corners (61, 291).
    Closed mouth MAR ~0.00-0.03, slightly parted ~0.03-0.08, open >0.10.
    """
    top = landmarks[13]     # inner upper lip
    bot = landmarks[14]     # inner lower lip
    left = landmarks[61]    # left corner
    right = landmarks[291]  # right corner
    vert = abs(top.y - bot.y) * img_h
    horiz = abs(right.x - left.x) * img_w
    if horiz < 1e-3:
        return 0.0
    return float(vert / horiz)


def _check_mouth_closed(image_bgr, face_rect):
    """Check mouth is closed using Mouth Aspect Ratio (MAR).

    MAR from MediaPipe inner-lip landmarks is a direct geometric
    measurement — no brightness/skin-tone bias like the prior heuristic.
    """
    h, w = image_bgr.shape[:2]
    landmarks = _landmarks(image_bgr)

    if landmarks is not None:
        try:
            mar = _mouth_aspect_ratio(landmarks, w, h)
        except (IndexError, AttributeError):
            mar = 0.0
        # Closed / neutrally closed: MAR < ~0.08. Open / teeth-showing: >0.10.
        if mar < 0.09:
            return True, "Mouth closed, neutral expression."
        return False, (
            f"Mouth appears open (gap ratio {mar:.2f}). "
            "Keep mouth closed with a neutral expression."
        )

    # --- Fallback: tightened brightness heuristic ---
    # Narrower mouth band + stricter thresholds to avoid false positives
    # from lip highlights on closed mouths.
    x, y, fw, fh = face_rect
    mouth_top = y + int(fh * 0.72)
    mouth_bottom = min(h, y + int(fh * 0.92))
    mouth_left = x + int(fw * 0.28)
    mouth_right = x + int(fw * 0.72)
    if mouth_top >= mouth_bottom or mouth_left >= mouth_right:
        return True, "Mouth closed, neutral expression."
    region = image_bgr[mouth_top:mouth_bottom, mouth_left:mouth_right]
    if region.size == 0:
        return True, "Mouth closed, neutral expression."
    lab = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    teeth_mask = (lab[:, :, 0] > 200) & (hsv[:, :, 1] < 40)
    teeth_pct = float(np.sum(teeth_mask)) / teeth_mask.size * 100
    if teeth_pct > 15:
        return False, "Teeth may be visible. Keep mouth closed with a neutral expression."
    return True, "Mouth closed, neutral expression."
