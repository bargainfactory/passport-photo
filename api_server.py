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
from processing.crop_resize import crop_and_center, crop_raw, mm_to_px, detect_crown_shift, apply_crown_shift, ensure_crown_clearance, flush_subject_bottom
from processing.validation import validate_photo
from processing.print_sheet import create_print_sheet
from processing.back_template import create_back_template, create_back_print_sheet
from processing.enhance import full_enhance_pipeline
from processing.straighten import straighten_image
from processing.inpaint import inpaint_region
from processing.upscale import upscale_pil
from processing.shoulder_extend import extend_shoulders
from config.constants import PREVIEW_DPI, DOWNLOAD_DPI
from utils.image_helpers import bytes_to_cv2, cv2_to_pil, pil_to_cv2, pil_to_bytes
from utils.currency import get_currency_for_country, convert_usd_cents, get_localized_pricing

app = FastAPI(title="PhotoPass Processing API")

# Allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.on_event("startup")
def _preload_models():
    """Lazy model load — first request triggers it. Keeps server start fast."""
    pass

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
    crown_top_mm: float | None = None
    print_sheet: PrintSheetConfig | None = None
    country_name: str | None = None  # used to opt into Canada back template


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
    # Optional guarantor back template
    back_b64: str | None = None        # single back panel @ DOWNLOAD_DPI
    back_sheet_b64: str | None = None  # ganged back sheet @ DOWNLOAD_DPI


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
    if req.crown_top_mm is not None:
        spec["crown_top_mm"] = req.crown_top_mm

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

    # --- Step 4: Crop ---
    straightened_pil = cv2_to_pil(straightened)
    enhanced_pil = cv2_to_pil(enhanced_full_bgr)

    # "Cropped Only" variant: plain geometric crop, no edits, subject flush with bottom
    orig_preview = crop_raw(straightened_pil, face_metrics, spec, dpi=PREVIEW_DPI)

    # Enhanced variant: crop → bg removal → composite → shoulders → crown → upscale
    enh_crop = crop_and_center(enhanced_pil, face_metrics, spec, dpi=PREVIEW_DPI)

    # --- Step 5: Background removal at high DPI ---
    # Crop the enhanced image at 1200 DPI (2× the preview DPI) and run
    # bg removal on this larger image. PyMatting alpha matting resolves
    # finer hair strands when given more pixels in the edge band.
    # The RGBA result is then downsampled to PREVIEW_DPI for the rest
    # of the pipeline.
    BG_REMOVAL_DPI = 1200
    enh_crop_hires = crop_and_center(
        enhanced_pil, face_metrics, spec, dpi=BG_REMOVAL_DPI,
    )
    enh_crop_bytes = pil_to_bytes(enh_crop_hires, fmt="PNG")
    enh_rgba_hires = remove_background(enh_crop_bytes)
    enh_rgba = enh_rgba_hires.resize(enh_crop.size, Image.LANCZOS)
    alpha_channel = enh_rgba.split()[3]

    # --- Step 6: Composite enhanced onto background color ---
    bg_color = tuple(req.bg_color)
    enh_preview = replace_background(enh_rgba, bg_color)
    enh_preview.info["dpi"] = (PREVIEW_DPI, PREVIEW_DPI)

    # --- Step 6a: Extend shoulders (enhanced only) ---
    import numpy as np
    alpha_np = np.array(alpha_channel)
    enh_preview = extend_shoulders(enh_preview, alpha_np, bg_color)
    enh_preview.info["dpi"] = (PREVIEW_DPI, PREVIEW_DPI)

    # --- Step 6a2: Flush subject to bottom edge ---
    enh_preview = flush_subject_bottom(enh_preview, bg_color, dpi=PREVIEW_DPI)

    # --- Step 6b: AI super-resolution (enhanced only) ---
    preview_size = enh_preview.size
    enh_upscaled = upscale_pil(enh_preview)
    enh_preview = enh_upscaled.resize(preview_size, Image.LANCZOS)
    enh_preview.info["dpi"] = (PREVIEW_DPI, PREVIEW_DPI)

    # --- Step 7: Validation ---
    # Detect face once on the cropped/enhanced preview. We deliberately
    # skip re-running eye detection (Haar) and recomputing metrics here
    # — the post-crop face_rect is sufficient for the geometric checks,
    # and tilt is already known from the original detection.
    enhanced_bgr = pil_to_cv2(enh_preview)
    val_face = detect_face(enhanced_bgr)
    val_metrics = (
        compute_face_metrics(val_face, enhanced_bgr.shape)
        if val_face is not None else face_metrics
    )
    validation_results = validate_photo(
        enhanced_bgr, val_face or face_rect, val_metrics, spec,
    )

    # --- Step 8: Downsample to download DPI ---
    download_w = mm_to_px(spec["width_mm"], DOWNLOAD_DPI)
    download_h = mm_to_px(spec["height_mm"], DOWNLOAD_DPI)

    # Downsample from the 2x upscaled version for maximum detail
    enh_processed = enh_upscaled.resize((download_w, download_h), Image.LANCZOS)
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

    # --- Step 9b: Guarantor back template (always generated) ---
    try:
        back_img = create_back_template(
            width_mm=spec["width_mm"],
            height_mm=spec["height_mm"],
            dpi=DOWNLOAD_DPI,
        )
        back_sheet_img = create_back_print_sheet(
            width_mm=spec["width_mm"],
            height_mm=spec["height_mm"],
            dpi=DOWNLOAD_DPI,
            orientation=sheet_kwargs["orientation"],
            cols=sheet_kwargs["cols"],
            rows=sheet_kwargs["rows"],
            separator_mm=sheet_kwargs["separator_mm"],
            y_offset_mm=sheet_kwargs["y_offset_mm"],
        )
        print(f"[back-template] Generated back={back_img.size} sheet={back_sheet_img.size}")
    except Exception as exc:
        import traceback
        print(f"[back-template] FAILED: {exc}")
        traceback.print_exc()
        back_img = None
        back_sheet_img = None

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
        back_b64=_b64(back_img) if back_img is not None else None,
        back_sheet_b64=_b64(back_sheet_img, quality=92) if back_sheet_img is not None else None,
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
    country_name: str = ""
    success_url: str = "http://localhost:3000?paid=true"
    cancel_url: str = "http://localhost:3000?cancelled=true"


_ITEM_PRICING_USD = {
    frozenset({"digital"}): (499, "Passport Photo — Digital Download"),
    frozenset({"sheet"}): (499, "Passport Photo — 4×6\" Print Sheet"),
    frozenset({"digital", "sheet"}): (899, "Passport Photo — Bundled Deal (Digital + 4×6\" Print Sheet)"),
}

_BASE_PRICES_USD = {"digital": 499, "sheet": 499, "bundle": 899}


@app.get("/api/pricing")
def get_pricing(country: str = ""):
    """Return localized pricing for the given country.

    The frontend calls this when the user reaches the download step so
    prices can be displayed in the customer's local currency.
    """
    pricing = get_localized_pricing(country, _BASE_PRICES_USD)
    return pricing


@app.post("/api/create-checkout")
def create_checkout(req: CheckoutRequest):
    """Create a Stripe Checkout Session in the customer's local currency."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe is not configured")

    valid = sorted({i for i in req.items if i in {"digital", "sheet"}})
    if not valid:
        raise HTTPException(400, "Must select at least one item")
    usd_cents, product_name = _ITEM_PRICING_USD[frozenset(valid)]

    currency = get_currency_for_country(req.country_name) if req.country_name else "usd"
    local_amount = convert_usd_cents(usd_cents, currency)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": product_name,
                        "description": "Compliant passport or visa photo — 350 DPI print-ready, JPEG + PNG",
                    },
                    "unit_amount": local_amount,
                },
                "quantity": 1,
            }],
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
