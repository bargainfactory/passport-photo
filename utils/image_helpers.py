"""Shared image conversion and utility functions."""

import io
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config.constants import DEFAULT_DPI


def bytes_to_cv2(image_bytes):
    """Convert raw image bytes to an OpenCV BGR numpy array."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def bytes_to_pil(image_bytes):
    """Convert raw image bytes to a PIL Image (RGB)."""
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def pil_to_bytes(pil_image, fmt="JPEG", quality=95, dpi=DEFAULT_DPI):
    """Convert a PIL Image to bytes in the specified format.

    Args:
        pil_image: PIL Image
        fmt: "JPEG" or "PNG"
        quality: JPEG quality (ignored for PNG)
        dpi: DPI metadata to embed

    Returns:
        bytes
    """
    buf = io.BytesIO()
    save_kwargs = {"dpi": (dpi, dpi)}
    if fmt.upper() == "JPEG":
        # Ensure RGB for JPEG (no alpha)
        if pil_image.mode == "RGBA":
            pil_image = pil_image.convert("RGB")
        save_kwargs["quality"] = quality
        save_kwargs["subsampling"] = 0  # Best quality
    pil_image.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


def cv2_to_pil(image_bgr):
    """Convert an OpenCV BGR array to a PIL RGB Image."""
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def pil_to_cv2(pil_image):
    """Convert a PIL RGB Image to an OpenCV BGR array."""
    rgb = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def add_watermark(pil_image, text="PREVIEW", opacity=80):
    """Add a diagonal watermark text overlay to a PIL Image.

    Args:
        pil_image: PIL Image (RGB)
        text: Watermark text
        opacity: Watermark opacity (0-255)

    Returns:
        New PIL Image with watermark applied
    """
    watermarked = pil_image.copy().convert("RGBA")
    overlay = Image.new("RGBA", watermarked.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Calculate font size relative to image
    font_size = max(20, min(watermarked.width, watermarked.height) // 6)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Center the text
    x = (watermarked.width - text_w) // 2
    y = (watermarked.height - text_h) // 2

    # Draw with semi-transparent red
    draw.text((x, y), text, fill=(255, 0, 0, opacity), font=font)

    # Also draw a second line rotated effect by drawing at angle offset
    x2 = x - text_w // 4
    y2 = y + text_h + font_size
    if y2 < watermarked.height:
        draw.text((x2, y2), text, fill=(255, 0, 0, opacity // 2), font=font)

    watermarked = Image.alpha_composite(watermarked, overlay)
    return watermarked.convert("RGB")
