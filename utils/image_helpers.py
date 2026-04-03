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
        if pil_image.mode == "RGBA":
            pil_image = pil_image.convert("RGB")
        save_kwargs["quality"] = quality
        save_kwargs["subsampling"] = 0
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


def add_watermark(pil_image, text="PREVIEW", opacity=70):
    """Add a diagonal watermark text overlay to a PIL Image.

    Creates a properly rotated diagonal watermark that tiles across the image
    for a professional preview appearance.

    Args:
        pil_image: PIL Image (RGB)
        text: Watermark text
        opacity: Watermark opacity (0-255)

    Returns:
        New PIL Image with watermark applied
    """
    img_w, img_h = pil_image.size

    # Create a large transparent overlay for the rotated text
    # Make it bigger than the image so rotation doesn't clip
    diag = int((img_w**2 + img_h**2) ** 0.5) + 100
    txt_layer = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Calculate font size relative to image (roughly 1/8th of shorter dimension)
    font_size = max(24, min(img_w, img_h) // 8)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Tile the watermark text across the overlay in a grid pattern
    spacing_x = text_w + font_size * 2
    spacing_y = text_h + font_size * 3

    y = 0
    row = 0
    while y < diag:
        x = -spacing_x // 2 if row % 2 else 0  # offset alternate rows
        while x < diag:
            # Primary text (semi-transparent red)
            draw.text(
                (x, y),
                text,
                fill=(220, 40, 40, opacity),
                font=font,
            )
            x += spacing_x
        y += spacing_y
        row += 1

    # Rotate the text layer -35 degrees
    txt_layer = txt_layer.rotate(35, resample=Image.BICUBIC, expand=False)

    # Crop to original image size from center
    cx = txt_layer.width // 2
    cy = txt_layer.height // 2
    left = cx - img_w // 2
    top = cy - img_h // 2
    txt_cropped = txt_layer.crop((left, top, left + img_w, top + img_h))

    # Composite onto the image
    watermarked = pil_image.copy().convert("RGBA")
    watermarked = Image.alpha_composite(watermarked, txt_cropped)
    return watermarked.convert("RGB")
