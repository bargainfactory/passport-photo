"""Head tilt correction and pose straightening.

Uses MediaPipe Face Mesh for precise landmark detection, then rotates
the image so the eye line is perfectly horizontal.
Falls back to Haar-cascade eye detection if MediaPipe is unavailable.
"""

import cv2
import math
import numpy as np
from PIL import Image

# Try MediaPipe for precise landmarks, fall back gracefully
_mp_face_mesh = None
_mp_available = False

try:
    import mediapipe as mp
    _mp_available = True
except ImportError:
    pass


def _get_face_mesh():
    """Lazy-load MediaPipe FaceMesh (heavy model, load once)."""
    global _mp_face_mesh
    if _mp_face_mesh is None and _mp_available:
        _mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )
    return _mp_face_mesh


def get_eye_centers_mediapipe(bgr_image):
    """Get precise eye center coordinates using MediaPipe Face Mesh.

    Returns:
        Tuple ((left_x, left_y), (right_x, right_y)) or None if detection fails.
        'Left' and 'right' refer to the subject's left and right eyes.
    """
    mesh = _get_face_mesh()
    if mesh is None:
        return None

    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    results = mesh.process(rgb)

    if not results.multi_face_landmarks:
        return None

    landmarks = results.multi_face_landmarks[0].landmark
    h, w = bgr_image.shape[:2]

    # MediaPipe landmark indices for eye centers:
    # Left iris center = 468, Right iris center = 473 (with refine_landmarks)
    # Fallback: Left eye inner corner = 133, outer = 33
    #           Right eye inner corner = 362, outer = 263
    try:
        # Refined iris landmarks (indices 468-472 left, 473-477 right)
        left_iris = landmarks[468]
        right_iris = landmarks[473]
        left_center = (int(left_iris.x * w), int(left_iris.y * h))
        right_center = (int(right_iris.x * w), int(right_iris.y * h))
    except (IndexError, AttributeError):
        # Fallback to eye corner midpoints
        le_inner = landmarks[133]
        le_outer = landmarks[33]
        re_inner = landmarks[362]
        re_outer = landmarks[263]
        left_center = (
            int((le_inner.x + le_outer.x) / 2 * w),
            int((le_inner.y + le_outer.y) / 2 * h),
        )
        right_center = (
            int((re_inner.x + re_outer.x) / 2 * w),
            int((re_inner.y + re_outer.y) / 2 * h),
        )

    return left_center, right_center


def get_eye_centers_haar(bgr_image, face_rect):
    """Get approximate eye centers using Haar cascade detection.

    Args:
        bgr_image: OpenCV BGR image
        face_rect: (x, y, w, h) face bounding box

    Returns:
        Tuple ((left_x, left_y), (right_x, right_y)) or None
    """
    if face_rect is None:
        return None

    x, y, w, h = face_rect
    face_roi = bgr_image[y:y + h, x:x + w]
    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml"
    )
    if eye_cascade.empty():
        return None

    eyes = eye_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5,
        minSize=(int(w * 0.1), int(h * 0.05)),
    )
    if len(eyes) < 2:
        return None

    # Sort by x to get left and right
    eyes_sorted = sorted(eyes, key=lambda e: e[0])
    le = eyes_sorted[0]
    re = eyes_sorted[-1]

    left_center = (x + le[0] + le[2] // 2, y + le[1] + le[3] // 2)
    right_center = (x + re[0] + re[2] // 2, y + re[1] + re[3] // 2)

    return left_center, right_center


def straighten_image(bgr_image, face_rect=None):
    """Straighten the image so the eye line is perfectly horizontal.

    Uses MediaPipe for precision when available, falls back to Haar.
    Only corrects tilts between 0.5° and 15° — ignores negligible
    or extreme tilts (which likely indicate profile shots).

    Args:
        bgr_image: OpenCV BGR numpy array
        face_rect: Optional (x, y, w, h) for Haar fallback

    Returns:
        Tuple (straightened_bgr, rotation_angle_degrees)
        rotation_angle_degrees is 0.0 if no correction was applied.
    """
    # Try MediaPipe first, then Haar
    eye_centers = get_eye_centers_mediapipe(bgr_image)
    if eye_centers is None:
        eye_centers = get_eye_centers_haar(bgr_image, face_rect)
    if eye_centers is None:
        return bgr_image, 0.0

    (lx, ly), (rx, ry) = eye_centers

    # Calculate tilt angle
    dx = rx - lx
    dy = ry - ly
    if abs(dx) < 1:
        return bgr_image, 0.0

    angle = math.degrees(math.atan2(dy, dx))

    # Only correct meaningful tilts (0.5° - 15°)
    if abs(angle) < 0.5 or abs(angle) > 15:
        return bgr_image, 0.0

    h, w = bgr_image.shape[:2]

    # Rotate around center of face (midpoint between eyes).
    # cv2.getRotationMatrix2D requires native Python floats — numpy scalar
    # types (e.g. np.int32 from Haar detections) trigger
    # "Can't parse 'center'. Sequence item with index 0 has a wrong type".
    center = (float((lx + rx) / 2.0), float((ly + ry) / 2.0))
    M = cv2.getRotationMatrix2D(center, float(angle), 1.0)

    # Compute new bounding box to avoid clipping
    cos_a = abs(M[0, 0])
    sin_a = abs(M[0, 1])
    new_w = int(h * sin_a + w * cos_a)
    new_h = int(h * cos_a + w * sin_a)

    # Adjust the rotation matrix for the new canvas size
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2

    rotated = cv2.warpAffine(
        bgr_image, M, (new_w, new_h),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    # Crop back to original size centered on the face
    cx, cy = new_w // 2, new_h // 2
    x1 = max(0, cx - w // 2)
    y1 = max(0, cy - h // 2)
    x2 = min(new_w, x1 + w)
    y2 = min(new_h, y1 + h)

    cropped = rotated[y1:y2, x1:x2]

    # Ensure output matches original dimensions
    if cropped.shape[:2] != (h, w):
        cropped = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)

    return cropped, float(angle)
