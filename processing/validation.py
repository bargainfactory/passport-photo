"""Photo validation checks for passport/visa compliance.

Runs a series of heuristic checks on the uploaded image and detected face
to flag potential issues before processing.
"""

import cv2
import numpy as np
from config.constants import MAX_TILT_DEGREES, MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT


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


def _check_eyes_open(image_bgr, face_rect):
    """Check if both eyes are open using eye aspect ratio heuristic.

    Detects eyes via Haar cascade, then checks if each eye region has
    enough dark pixels (iris/pupil) to indicate the eye is open.
    """
    x, y, fw, fh = face_rect

    # Eye region: upper 20-45% of face
    eye_top = y + int(fh * 0.18)
    eye_bottom = y + int(fh * 0.45)
    eye_left = x + int(fw * 0.05)
    eye_right = x + int(fw * 0.95)

    if eye_top >= eye_bottom or eye_left >= eye_right:
        return True, "Unable to assess eyes."

    eye_region = image_bgr[eye_top:eye_bottom, eye_left:eye_right]
    if eye_region.size == 0:
        return True, "Unable to assess eyes."

    gray_eyes = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)

    # Use Haar cascade for eye detection
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml"
    )
    eyes = eye_cascade.detectMultiScale(
        gray_eyes, scaleFactor=1.1, minNeighbors=3,
        minSize=(int(fw * 0.06), int(fh * 0.03)),
    )

    if len(eyes) < 2:
        # Fewer than 2 eyes detected — likely closed or obscured
        # Double-check with eye-open cascade
        eye_open_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
        )
        eyes_open = eye_open_cascade.detectMultiScale(
            gray_eyes, scaleFactor=1.1, minNeighbors=3,
            minSize=(int(fw * 0.06), int(fh * 0.03)),
        )
        if len(eyes_open) < 2:
            return False, "Eyes may be closed. Keep both eyes open and clearly visible."

    return True, "Both eyes appear open."


def _check_mouth_closed(image_bgr, face_rect):
    """Check if the mouth is closed (no teeth showing).

    Looks at the lower face region for bright white pixels that indicate
    exposed teeth against the darker lip/skin area.
    """
    x, y, fw, fh = face_rect
    h, w = image_bgr.shape[:2]

    # Mouth region: lower 30% of face, center 60% width
    mouth_top = y + int(fh * 0.65)
    mouth_bottom = min(h, y + int(fh * 1.0))
    mouth_left = x + int(fw * 0.2)
    mouth_right = x + int(fw * 0.8)

    if mouth_top >= mouth_bottom or mouth_left >= mouth_right:
        return True, "Unable to assess mouth."

    mouth_region = image_bgr[mouth_top:mouth_bottom, mouth_left:mouth_right]
    if mouth_region.size == 0:
        return True, "Unable to assess mouth."

    # Convert to LAB for luminance analysis
    lab = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]

    # Teeth are distinctly brighter than surrounding lip/skin area
    # High luminance + low saturation = likely teeth
    hsv = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]

    # Teeth: bright (L > 180) and low saturation (S < 60)
    teeth_mask = (l_channel > 180) & (saturation < 60)
    teeth_pct = float(np.sum(teeth_mask)) / teeth_mask.size * 100

    if teeth_pct > 8:
        return False, f"Teeth may be visible ({teeth_pct:.0f}% bright pixels in mouth area). Keep mouth closed with a neutral expression."

    return True, "Mouth closed, neutral expression."
