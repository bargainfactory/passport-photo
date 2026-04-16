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
from PIL import Image

from processing.face_detection import detect_face, detect_eyes, compute_face_metrics
from processing.background import remove_background, replace_background
from processing.crop_resize import crop_and_center, mm_to_px
from processing.validation import validate_photo
from processing.print_sheet import create_print_sheet
from processing.enhance import full_enhance_pipeline
from processing.straighten import straighten_image
from processing.inpaint import inpaint_region
from config.constants import PREVIEW_DPI, DOWNLOAD_DPI
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


class PrintSheetConfig(BaseModel):
    """Per-country overrides for the print-sheet layout."""
    orientation: str = "landscape"  # "landscape" or "portrait"
    cols: int = 3
    rows: int = 2
    separator_mm: float | None = None  # None = DPI-derived default
    y_offset_mm: float = 0.0  # nudge the grid down by this many mm


class ProcessRequest(BaseModel):
    """Request body for photo processing."""
    image_b64: str  # base64-encoded image (data URL or raw b64)
    width_mm: int
    height_mm: int
    bg_color: list[int]  # [R, G, B]
    head_pct: list[int]  # [min, max]
    eye_line_pct: list[int]  # [min, max]
    print_sheet: PrintSheetConfig | None = None


class ProcessResponse(BaseModel):
    """Response with processed images and validation results.

    Two variants are returned so the user can choose:
      - *_enhanced_*: full AI enhancement pipeline applied
      - *_original_*: background replaced + cropped to spec, no enhancement
    Each is available at PREVIEW_DPI (crisp on-screen) and DOWNLOAD_DPI
    (print-ready download).
    """
    # Enhanced variants
    preview_b64: str         # enhanced @ PREVIEW_DPI (display)
    preview_sheet_b64: str   # enhanced sheet @ PREVIEW_DPI
    processed_b64: str       # enhanced @ DOWNLOAD_DPI (print)
    sheet_b64: str           # enhanced sheet @ DOWNLOAD_DPI
    # Original (unenhanced) variants
    original_preview_b64: str
    original_preview_sheet_b64: str
    original_processed_b64: str
    original_sheet_b64: str
    validation: list[dict]


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

    Pipeline order (2025-04 revision — "crop-first" for sharper edges):
    1. Face detection on original
    2. Head straightening (tilt correction)
    3. Enhancement on full frame (face-aware lighting, smoothing, sharpen)
    4. Crop BOTH variants to 600 DPI (original background still present)
    5. Background removal on the 600 DPI crop → alpha mask at output res
    6. Composite onto spec bg_color
    7. Validation checks
    8. Downsample preview (600 DPI) → download (350 DPI)
    9. Generate print sheets

    Running bg removal AFTER cropping to output resolution means the
    segmentation mask is generated at 600 DPI rather than at the camera's
    (often much higher) resolution then downscaled. This preserves sharp
    subject edges — the mask-to-output ratio is close to 1:1.
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

    if abs(tilt_angle) > 0.5:
        face_rect = detect_face(straightened)
        if face_rect is None:
            straightened = image_bgr
            face_rect = detect_face(image_bgr)
            if face_rect is None:
                raise HTTPException(422, "Face lost after straightening. Try a clearer photo.")

    # --- Step 3: Face metrics + enhancement on the full frame ---
    eyes = detect_eyes(straightened, face_rect)
    face_metrics = compute_face_metrics(face_rect, straightened.shape, eyes)

    enhanced_full_bgr = full_enhance_pipeline(straightened, face_rect)

    # --- Step 4: Crop both variants to 600 DPI (bg still present) ---
    straightened_pil = cv2_to_pil(straightened)
    enhanced_pil = cv2_to_pil(enhanced_full_bgr)

    orig_crop = crop_and_center(straightened_pil, face_metrics, spec, dpi=PREVIEW_DPI)
    enh_crop = crop_and_center(enhanced_pil, face_metrics, spec, dpi=PREVIEW_DPI)

    # --- Step 5: Background removal at 600 DPI ---
    # Single segmentation pass on the original crop; the alpha mask is
    # shared with the enhanced variant (identical crop geometry).
    orig_crop_bytes = pil_to_bytes(orig_crop, fmt="PNG")
    rgba_crop = remove_background(orig_crop_bytes)
    alpha_channel = rgba_crop.split()[3]

    # Apply same alpha to enhanced crop
    enh_crop_rgba = enh_crop.convert("RGBA")
    enh_rgba = Image.merge("RGBA", (*enh_crop_rgba.split()[:3], alpha_channel))

    # --- Step 6: Composite onto background color ---
    bg_color = tuple(req.bg_color)
    orig_preview = replace_background(rgba_crop, bg_color)
    enh_preview = replace_background(enh_rgba, bg_color)
    orig_preview.info["dpi"] = (PREVIEW_DPI, PREVIEW_DPI)
    enh_preview.info["dpi"] = (PREVIEW_DPI, PREVIEW_DPI)

    # --- Step 7: Validation ---
    enhanced_bgr = pil_to_cv2(enh_preview)
    val_face = detect_face(enhanced_bgr)
    if val_face is not None:
        val_eyes = detect_eyes(enhanced_bgr, val_face)
        val_metrics = compute_face_metrics(val_face, enhanced_bgr.shape, val_eyes)
    else:
        val_metrics = face_metrics
    validation_results = validate_photo(
        enhanced_bgr, val_face or face_rect, val_metrics, spec,
    )

    # --- Step 8: Downsample to download DPI ---
    download_w = mm_to_px(spec["width_mm"], DOWNLOAD_DPI)
    download_h = mm_to_px(spec["height_mm"], DOWNLOAD_DPI)

    enh_processed = enh_preview.resize((download_w, download_h), Image.LANCZOS)
    enh_processed.info["dpi"] = (DOWNLOAD_DPI, DOWNLOAD_DPI)

    orig_processed = orig_preview.resize((download_w, download_h), Image.LANCZOS)
    orig_processed.info["dpi"] = (DOWNLOAD_DPI, DOWNLOAD_DPI)

    # --- Step 9: Print sheets for both variants at both DPIs ---
    ps = req.print_sheet
    sheet_kwargs = {
        "orientation": ps.orientation if ps else "landscape",
        "cols": ps.cols if ps else 3,
        "rows": ps.rows if ps else 2,
        "separator_mm": ps.separator_mm if ps else None,
        "y_offset_mm": ps.y_offset_mm if ps else 0.0,
    }
    enh_preview_sheet = create_print_sheet(enh_preview, dpi=PREVIEW_DPI, **sheet_kwargs)
    enh_sheet = create_print_sheet(enh_processed, dpi=DOWNLOAD_DPI, **sheet_kwargs)
    orig_preview_sheet = create_print_sheet(orig_preview, dpi=PREVIEW_DPI, **sheet_kwargs)
    orig_sheet = create_print_sheet(orig_processed, dpi=DOWNLOAD_DPI, **sheet_kwargs)

    def _b64(pil_img, quality=95):
        return "data:image/jpeg;base64," + base64.b64encode(
            pil_to_bytes(pil_img, fmt="JPEG", quality=quality)
        ).decode()

    return ProcessResponse(
        preview_b64=_b64(enh_preview),
        preview_sheet_b64=_b64(enh_preview_sheet, quality=92),
        processed_b64=_b64(enh_processed),
        sheet_b64=_b64(enh_sheet),
        original_preview_b64=_b64(orig_preview),
        original_preview_sheet_b64=_b64(orig_preview_sheet, quality=92),
        original_processed_b64=_b64(orig_processed),
        original_sheet_b64=_b64(orig_sheet),
        validation=[
            {"check": str(v["check"]), "passed": bool(v["passed"]), "message": str(v["message"])}
            for v in validation_results
        ],
    )


class CheckoutRequest(BaseModel):
    """Request body for creating a Stripe checkout session.

    items contains any subset of {"digital", "sheet"} — the user can
    buy either product on its own or both together (bundle-priced).
    """
    items: list[str] = ["digital"]
    success_url: str = "http://localhost:3000?paid=true"
    cancel_url: str = "http://localhost:3000?cancelled=true"


# (items-key, price cents, Stripe product name)
_ITEM_PRICING = {
    frozenset({"digital"}): (499, "Passport Photo — Digital Download"),
    frozenset({"sheet"}): (499, "Passport Photo — 4x6\" Print Sheet"),
    frozenset({"digital", "sheet"}): (799, "Passport Photo — Digital + 4x6\" Print Sheet"),
}


@app.post("/api/create-checkout")
def create_checkout(req: CheckoutRequest):
    """Create a Stripe Checkout Session and return the URL."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe is not configured")

    valid = sorted({i for i in req.items if i in {"digital", "sheet"}})
    if not valid:
        raise HTTPException(400, "Must select at least one item")
    price_cents, product_name = _ITEM_PRICING[frozenset(valid)]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product_name,
                        "description": "Compliant passport or visa photo — 350 DPI print-ready, JPEG + PNG",
                    },
                    "unit_amount": price_cents,
                },
                "quantity": 1,
            }],
            # Persist what was bought so verify-payment can gate downloads
            # to the purchased items only.
            metadata={"items": ",".join(valid)},
            success_url=req.success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@app.get("/api/verify-payment")
def verify_payment(session_id: str):
    """Verify a Stripe checkout session was paid and report purchased items."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe is not configured")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        items_str = (session.metadata or {}).get("items", "") if session.metadata else ""
        items = [i for i in items_str.split(",") if i]
        return {
            "paid": session.payment_status == "paid",
            "items": items,
        }
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


class InpaintRequest(BaseModel):
    """Request body for content-aware fill."""
    image_b64: str  # data URL of the image to edit
    mask_b64: str   # data URL of the mask (white = fill, black = keep)
    radius: int = 5


class InpaintResponse(BaseModel):
    image_b64: str


@app.post("/api/inpaint", response_model=InpaintResponse)
def api_inpaint(req: InpaintRequest):
    """Content-aware fill the masked region of an image."""
    try:
        image_bytes = _decode_image(req.image_b64)
        mask_bytes = _decode_image(req.mask_b64)
    except Exception:
        raise HTTPException(400, "Invalid image or mask data")

    image_bgr = bytes_to_cv2(image_bytes)
    if image_bgr is None:
        raise HTTPException(400, "Could not decode image")

    import numpy as np
    mask_arr = np.frombuffer(mask_bytes, np.uint8)
    mask_bgr = __import__("cv2").imdecode(mask_arr, __import__("cv2").IMREAD_GRAYSCALE)
    if mask_bgr is None:
        raise HTTPException(400, "Could not decode mask")

    try:
        result_bgr = inpaint_region(image_bgr, mask_bgr, radius=max(1, min(20, req.radius)))
    except Exception as e:
        raise HTTPException(500, f"Inpaint failed: {e}")

    result_pil = cv2_to_pil(result_bgr)
    buf = io.BytesIO()
    result_pil.save(buf, format="JPEG", quality=95)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return InpaintResponse(image_b64="data:image/jpeg;base64," + b64)


@app.get("/api/health")
def health():
    return {"status": "ok"}
