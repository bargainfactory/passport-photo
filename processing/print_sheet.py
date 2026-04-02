"""Generate print-ready photo sheets (2x2 or 4-up layouts on 4x6 inch paper)."""

from PIL import Image
from config.constants import (
    DEFAULT_DPI,
    PRINT_SHEET_WIDTH_IN,
    PRINT_SHEET_HEIGHT_IN,
    PRINT_SHEET_MARGIN_MM,
)
from processing.crop_resize import mm_to_px


def create_print_sheet(photo, layout="2x2", dpi=DEFAULT_DPI):
    """Create a 4x6 inch print sheet with multiple copies of the photo.

    Args:
        photo: PIL Image of the processed passport photo
        layout: "2x2" (4 photos) or "2x1" (2 photos)
        dpi: Output DPI (default 300)

    Returns:
        PIL Image of the print sheet at the specified DPI
    """
    sheet_w = int(PRINT_SHEET_WIDTH_IN * dpi)
    sheet_h = int(PRINT_SHEET_HEIGHT_IN * dpi)
    margin = mm_to_px(PRINT_SHEET_MARGIN_MM, dpi)

    # Create white canvas
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))

    photo_w, photo_h = photo.size

    if layout == "2x2":
        positions = _compute_grid_positions(sheet_w, sheet_h, photo_w, photo_h, 2, 2, margin)
    else:  # "2x1"
        positions = _compute_grid_positions(sheet_w, sheet_h, photo_w, photo_h, 2, 1, margin)

    for x, y in positions:
        sheet.paste(photo, (x, y))

    # Draw light cutting guides
    sheet = _draw_cutting_guides(sheet, positions, photo_w, photo_h, margin)

    sheet.info["dpi"] = (dpi, dpi)
    return sheet


def _compute_grid_positions(sheet_w, sheet_h, photo_w, photo_h, cols, rows, margin):
    """Compute centered grid positions for photos on the sheet."""
    total_w = cols * photo_w + (cols - 1) * margin
    total_h = rows * photo_h + (rows - 1) * margin

    start_x = (sheet_w - total_w) // 2
    start_y = (sheet_h - total_h) // 2

    # Clamp to positive
    start_x = max(margin, start_x)
    start_y = max(margin, start_y)

    positions = []
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * (photo_w + margin)
            y = start_y + row * (photo_h + margin)
            if x + photo_w <= sheet_w and y + photo_h <= sheet_h:
                positions.append((x, y))

    return positions


def _draw_cutting_guides(sheet, positions, photo_w, photo_h, margin):
    """Draw subtle dashed cutting guide lines around each photo position."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(sheet)
    guide_color = (200, 200, 200)  # Light gray
    guide_len = max(5, margin // 2)

    for x, y in positions:
        corners = [
            (x, y),                           # top-left
            (x + photo_w, y),                  # top-right
            (x, y + photo_h),                  # bottom-left
            (x + photo_w, y + photo_h),        # bottom-right
        ]
        for cx, cy in corners:
            # Horizontal marks
            draw.line([(cx - guide_len, cy), (cx + guide_len, cy)], fill=guide_color, width=1)
            # Vertical marks
            draw.line([(cx, cy - guide_len), (cx, cy + guide_len)], fill=guide_color, width=1)

    return sheet
