"""Face detection using OpenCV Haar cascades.

Detects the largest face in an image and computes positioning metrics
used for cropping and validation.
"""

import cv2
import numpy as np
from functools import lru_cache
from config.constants import FACE_SCALE_FACTOR, FACE_MIN_NEIGHBORS, FACE_MIN_SIZE

# Optional Streamlit caching — use lru_cache when running under FastAPI
try:
    import streamlit as st
    _cache = st.cache_resource
except Exception:
    _cache = lru_cache(maxsize=1)


@_cache
def _load_face_cascade():
    """Load and cache the Haar cascade classifier."""
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        raise RuntimeError(f"Failed to load cascade from {cascade_path}")
    return cascade


@_cache
def _load_eye_cascade():
    """Load and cache the eye Haar cascade classifier."""
    cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    return cascade


def detect_face(image_bgr):
    """Detect the largest face in a BGR image.

    Args:
        image_bgr: numpy array in BGR format (as loaded by OpenCV)

    Returns:
        Tuple (x, y, w, h) of the largest face bounding box, or None if no face found.
    """
    cascade = _load_face_cascade()
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=FACE_SCALE_FACTOR,
        minNeighbors=FACE_MIN_NEIGHBORS,
        minSize=FACE_MIN_SIZE,
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    if len(faces) == 0:
        return None

    # Return the largest face by area
    largest = max(faces, key=lambda f: f[2] * f[3])
    return tuple(int(v) for v in largest)


def detect_eyes(image_bgr, face_rect):
    """Detect eyes within a face region.

    Args:
        image_bgr: Full image in BGR format
        face_rect: (x, y, w, h) face bounding box

    Returns:
        List of (ex, ey, ew, eh) eye rectangles relative to the full image,
        or empty list if none found.
    """
    cascade = _load_eye_cascade()
    if cascade.empty():
        return []

    x, y, w, h = face_rect
    face_roi = image_bgr[y:y + h, x:x + w]
    gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

    eyes = cascade.detectMultiScale(
        gray_roi,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(int(w * 0.1), int(h * 0.05)),
    )

    # Convert coordinates back to full image space
    result = []
    for (ex, ey, ew, eh) in eyes:
        result.append((x + ex, y + ey, ew, eh))
    return result


def compute_face_metrics(face_rect, image_shape, eyes=None):
    """Compute positioning metrics from a face detection.

    Args:
        face_rect: (x, y, w, h) face bounding box
        image_shape: (height, width, ...) of the source image
        eyes: Optional list of eye rects for more accurate eye-line computation

    Returns:
        dict with keys:
            center_x, center_y: Face center coordinates
            eye_line_y: Estimated Y coordinate of the eye line
            head_top_y: Estimated top of head
            chin_y: Estimated chin position
            head_height: Estimated full head height (top to chin)
            face_width: Detected face width
            tilt_degrees: Estimated head tilt (0 if eyes not detected)
    """
    x, y, w, h = face_rect
    img_h, img_w = image_shape[:2]

    center_x = x + w // 2
    center_y = y + h // 2

    # Haar cascade face box typically starts at forehead and ends at chin.
    # Eyes are roughly 35% from the top of the detected box.
    eye_line_y = y + int(h * 0.35)

    # Head top (including hair) is typically ~30% above the face box top.
    # Using 15% here under-estimates head height, causing the crop to
    # over-scale the head and clip the hair.
    head_top_y = max(0, y - int(h * 0.30))

    # Chin sits slightly below the Haar box bottom (box ends near lower lip).
    chin_y = min(img_h, y + h + int(h * 0.05))

    # Full head height estimate (top of head to chin)
    head_height = chin_y - head_top_y

    # Compute tilt from eye positions if available
    tilt_degrees = 0.0
    if eyes and len(eyes) >= 2:
        # Sort eyes by x to get left and right
        sorted_eyes = sorted(eyes, key=lambda e: e[0])
        left_eye = sorted_eyes[0]
        right_eye = sorted_eyes[-1]
        le_center = (left_eye[0] + left_eye[2] // 2, left_eye[1] + left_eye[3] // 2)
        re_center = (right_eye[0] + right_eye[2] // 2, right_eye[1] + right_eye[3] // 2)
        dx = re_center[0] - le_center[0]
        dy = re_center[1] - le_center[1]
        if dx != 0:
            tilt_degrees = abs(np.degrees(np.arctan2(dy, dx)))

        # Use actual eye positions for eye-line
        eye_line_y = (le_center[1] + re_center[1]) // 2

    return {
        "center_x": center_x,
        "center_y": center_y,
        "eye_line_y": eye_line_y,
        "head_top_y": head_top_y,
        "chin_y": chin_y,
        "head_height": head_height,
        "face_width": w,
        "tilt_degrees": tilt_degrees,
    }
