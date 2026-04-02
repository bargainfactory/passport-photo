"""Background removal and replacement using rembg and Pillow."""

from PIL import Image
from rembg import remove
import io


def remove_background(image_bytes):
    """Remove the background from a photo using rembg (U2-Net).

    Args:
        image_bytes: Raw image bytes (JPEG/PNG)

    Returns:
        PIL Image in RGBA mode with transparent background
    """
    result_bytes = remove(image_bytes)
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")


def replace_background(rgba_image, bg_color_rgb):
    """Composite an RGBA image onto a solid color background.

    Args:
        rgba_image: PIL Image in RGBA mode (transparent background)
        bg_color_rgb: Tuple (R, G, B) for the target background color

    Returns:
        PIL Image in RGB mode with the solid background applied
    """
    background = Image.new("RGB", rgba_image.size, bg_color_rgb)
    background.paste(rgba_image, mask=rgba_image.split()[3])  # Use alpha as mask
    return background
