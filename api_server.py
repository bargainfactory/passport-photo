"""FastAPI backend server for passport photo processing.

Wraps the existing Python processing pipeline (rembg, OpenCV, Pillow)
and exposes it as a REST API for the Next.js frontend.

Run with: uvicorn api_server:app --port 8000 --reload
"""

import io
import os
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import stripe

from processing.face_detection import detect_face, detect_eyes, compute_face_metrics
from processing.background import remove_background, replace_background
from processing.crop_resize import crop_and_center
from processing.validation import validate_photo
from processing.print_sheet import create_print_sheet
from processing.enhance import full_enhance_pipeline
from processing.straighten import straighten_image
from utils.image_helpers import bytes_to_cv2, cv2_to_pil, pil_to_cv2, pil_to_bytes

app = FastAPI(title="PhotoPass Processing API")

# Allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- Stripe configuration ---
def _load_stripe_key():
    """Load Stripe secret key from .streamlit/secrets.toml or env."""
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if key:
        return key
    try:
        import tomllib
        with open(".streamlit/secrets.toml", "rb") as f:
            secrets = tomllib.load(f)
        return secrets.get("STRIPE_SECRET_KEY", "")
    except Exception:
        return ""

stripe.api_key = _load_stripe_key()


class ProcessRequest(BaseModel):
    """Request body for photo processing."""
    image_b64: str  # base64-encoded image (data URL or raw b64)
    width_mm: int
    height_mm: int
    bg_color: list[int]  # [R, G, B]
    head_pct: list[int]  # [min, max]
    eye_line_pct: list[int]  # [min, max]


class ProcessResponse(BaseModel):
    """Response with processed images and validation results."""
    processed_b64: str  # base64 JPEG of single cropped photo
    sheet_b64: str  # base64 JPEG of 2x2 print sheet
    validation: list[dict]  # [{check, passed, message}, ...]


def _decode_image(image_b64: str) -> bytes:
    """Decode a base64 image string (with or without data URL prefix)."""
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    return base64.b64decode(image_b64)


@app.post("/api/process", response_model=ProcessResponse)
def process_photo(req: ProcessRequest):
    """Full processing pipeline: detect, validate, remove bg, crop, sheet."""

    # Decode image
    try:
        image_bytes = _decode_image(req.image_b64)
    except Exception:
        raise HTTPException(400, "Invalid image data")

    # Build spec dict
    spec = {
        "width_mm": req.width_mm,
        "height_mm": req.height_mm,
        "bg_color": tuple(req.bg_color),
        "head_pct": tuple(req.head_pct),
        "eye_line_pct": tuple(req.eye_line_pct),
    }

    try:
        return _run_pipeline(image_bytes, spec, req)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Processing failed: {str(e)}")


def _run_pipeline(image_bytes: bytes, spec: dict, req: ProcessRequest) -> ProcessResponse:
    """Run the full AI processing pipeline.

    Pipeline order:
    1. Face detection on original
    2. Head straightening (tilt correction via MediaPipe/Haar)
    3. Lighting correction + shadow removal + white balance
    4. Validation checks (on corrected image)
    5. Background removal (rembg ISNet + alpha refinement)
    6. Replace background with spec color
    7. Skin enhancement + contrast + print sharpening
    8. Crop and center to spec dimensions
    9. Generate 4x6 print sheet
    """

    # --- Step 1: Decode & detect face ---
    image_bgr = bytes_to_cv2(image_bytes)
    if image_bgr is None:
        raise HTTPException(400, "Could not decode image. Upload a valid JPEG or PNG.")

    face_rect = detect_face(image_bgr)
    if face_rect is None:
        raise HTTPException(
            422,
            "No face detected. Ensure your face is clearly visible, front-facing, and well-lit.",
        )

    # --- Step 2: Straighten head tilt ---
    straightened, tilt_angle = straighten_image(image_bgr, face_rect)

    # Re-detect face after straightening (coordinates shifted)
    if abs(tilt_angle) > 0.5:
        face_rect = detect_face(straightened)
        if face_rect is None:
            # Fall back to un-straightened if re-detection fails
            straightened = image_bgr
            face_rect = detect_face(image_bgr)
            if face_rect is None:
                raise HTTPException(422, "Face lost after straightening. Try a clearer photo.")

    # --- Step 3: Lighting correction ---
    corrected = full_enhance_pipeline(straightened, face_rect)

    # --- Step 4: Validation (on corrected image) ---
    eyes = detect_eyes(corrected, face_rect)
    face_metrics = compute_face_metrics(face_rect, corrected.shape, eyes)
    validation_results = validate_photo(corrected, face_rect, face_metrics, spec)

    # --- Step 5: Background removal ---
    # Encode corrected image to bytes for rembg
    corrected_pil = cv2_to_pil(corrected)
    corrected_bytes = pil_to_bytes(corrected_pil, fmt="PNG")
    rgba_image = remove_background(corrected_bytes)

    # --- Step 6: Replace background with spec color ---
    bg_color = tuple(req.bg_color)
    rgb_image = replace_background(rgba_image, bg_color)

    # --- Step 7: Re-detect face on final composite for accurate crop ---
    rgb_bgr = pil_to_cv2(rgb_image)
    new_face = detect_face(rgb_bgr)
    if new_face is not None:
        new_eyes = detect_eyes(rgb_bgr, new_face)
        new_metrics = compute_face_metrics(new_face, rgb_bgr.shape, new_eyes)
    else:
        new_metrics = face_metrics

    # --- Step 8: Crop and center to spec ---
    processed = crop_and_center(rgb_image, new_metrics, spec)

    # --- Step 9: Generate print sheet ---
    sheet = create_print_sheet(processed, layout="2x2")

    # Encode results
    processed_bytes = pil_to_bytes(processed, fmt="JPEG", quality=95)
    sheet_bytes = pil_to_bytes(sheet, fmt="JPEG", quality=95)

    return ProcessResponse(
        processed_b64="data:image/jpeg;base64," + base64.b64encode(processed_bytes).decode(),
        sheet_b64="data:image/jpeg;base64," + base64.b64encode(sheet_bytes).decode(),
        validation=[
            {"check": str(v["check"]), "passed": bool(v["passed"]), "message": str(v["message"])}
            for v in validation_results
        ],
    )


class CheckoutRequest(BaseModel):
    """Request body for creating a Stripe checkout session."""
    success_url: str = "http://localhost:3000?paid=true"
    cancel_url: str = "http://localhost:3000?cancelled=true"


@app.post("/api/create-checkout")
def create_checkout(req: CheckoutRequest):
    """Create a Stripe Checkout Session and return the URL."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe is not configured")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Passport/Visa Photo Download",
                        "description": (
                            "Compliant passport or visa photo — "
                            "digital download (JPEG + PNG, 300 DPI, print sheet included)"
                        ),
                    },
                    "unit_amount": 499,  # $4.99
                },
                "quantity": 1,
            }],
            success_url=req.success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@app.get("/api/verify-payment")
def verify_payment(session_id: str):
    """Verify a Stripe checkout session was paid."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe is not configured")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {"paid": session.payment_status == "paid"}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


# --- Suggestion box ---
import json
from datetime import datetime
from pathlib import Path

SUGGESTIONS_FILE = Path(__file__).parent / "data" / "suggestions.json"


class SuggestionRequest(BaseModel):
    """Request body for submitting a suggestion."""
    message: str
    category: str = "general"  # general, quality, feature, bug
    rating: int | None = None  # 1-5 optional satisfaction rating


@app.post("/api/suggestions")
def submit_suggestion(req: SuggestionRequest):
    """Save a customer suggestion to the local suggestions log.

    Suggestions are appended to data/suggestions.json for the team
    to review and prioritize improvements.
    """
    message = req.message.strip()
    if not message:
        raise HTTPException(400, "Suggestion cannot be empty")
    if len(message) > 2000:
        raise HTTPException(400, "Suggestion is too long (max 2000 characters)")

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "category": req.category,
        "message": message,
        "rating": req.rating,
    }

    # Ensure data directory exists
    SUGGESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing suggestions
    suggestions = []
    if SUGGESTIONS_FILE.exists():
        try:
            suggestions = json.loads(SUGGESTIONS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            suggestions = []

    suggestions.append(entry)
    SUGGESTIONS_FILE.write_text(
        json.dumps(suggestions, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {"ok": True, "count": len(suggestions)}


@app.get("/api/health")
def health():
    return {"status": "ok"}
