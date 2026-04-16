"""Generate print-ready photo sheets on 4x6 inch paper."""

from PIL import Image
from config.constants import (
    DEFAULT_DPI,
    PRINT_SHEET_WIDTH_IN,
    PRINT_SHEET_HEIGHT_IN,
    PRINT_SHEET_MARGIN_MM,
)
from processing.crop_resize import mm_to_px


def create_print_sheet(photo, layout="3x2", dpi=DEFAULT_DPI):
    """Create a 4x6 inch print sheet tiled with copies of the photo.

    Args:
        photo: PIL Image of the processed passport photo
        layout: "3x2" (6 photos, default), "2x2" (4 photos), or "2x1"
        dpi: Output DPI (default 350)

    Returns:
        PIL Image of the print sheet at the specified DPI
    """
    sheet_w = int(PRINT_SHEET_WIDTH_IN * dpi)
    sheet_h = int(PRINT_SHEET_HEIGHT_IN * dpi)
    margin = mm_to_px(PRINT_SHEET_MARGIN_MM, dpi)

    # Create white canvas
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))

    if layout == "3x2":
        cols, rows = 3, 2
    elif layout == "2x2":
        cols, rows = 2, 2
    else:  # "2x1"
        cols, rows = 2, 1

    photo_w, photo_h = photo.size

    # Auto-scale the photo if the requested size doesn't fit the grid.
    # Keeps larger passport photos (e.g. 51x51mm US) from overflowing
    # the 6x4" sheet when ganged 6-up.
    avail_w = sheet_w - 2 * margin - (cols - 1) * margin
    avail_h = sheet_h - 2 * margin - (rows - 1) * margin
    max_w = avail_w // cols
    max_h = avail_h // rows
    if photo_w > max_w or photo_h > max_h:
        scale = min(max_w / photo_w, max_h / photo_h)
        photo_w = int(photo_w * scale)
        photo_h = int(photo_h * scale)
        photo = photo.resize((photo_w, photo_h), Image.LANCZOS)

    positions = _compute_grid_positions(sheet_w, sheet_h, photo_w, photo_h, cols, rows, margin)

    for x, y in positions:
        sheet.paste(photo, (x, y))

    sheet = _draw_cutting_lines(sheet, positions, photo_w, photo_h, margin, cols, rows, dpi)

    sheet.info["dpi"] = (dpi, dpi)
    return sheet


def _compute_grid_positions(sheet_w, sheet_h, photo_w, photo_h, cols, rows, margin):
    """Compute centered grid positions for photos on the sheet."""
    total_w = cols * photo_w + (cols - 1) * margin
    total_h = rows * photo_h + (rows - 1) * margin

    start_x = (sheet_w - total_w) // 2
    start_y = (sheet_h - total_h) // 2

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


def _draw_cutting_lines(sheet, positions, photo_w, photo_h, margin, cols, rows, dpi):
    """Draw thin grey lines between photos to delineate each cell."""
    from PIL import ImageDraw

    if not positions:
        return sheet

    draw = ImageDraw.Draw(sheet)
    color = (180, 180, 180)
    lw = max(1, dpi // 175)  # 2px at 350 DPI, 3px at 600 DPI

    start_x, start_y = positions[0]
    grid_w = cols * photo_w + (cols - 1) * margin
    grid_h = rows * photo_h + (rows - 1) * margin

    # Vertical separators centered in each column gap
    for col in range(1, cols):
        x = start_x + col * photo_w + (col - 1) * margin + margin // 2
        draw.line([(x, start_y), (x, start_y + grid_h)], fill=color, width=lw)

    # Horizontal separators centered in each row gap
    for row in range(1, rows):
        y = start_y + row * photo_h + (row - 1) * margin + margin // 2
        draw.line([(start_x, y), (start_x + grid_w, y)], fill=color, width=lw)

    return sheet
