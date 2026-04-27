"""Back-of-photo guarantor templates (Canadian passport spec).

Two outputs:
  * `create_back_template`  – a single back panel at the photo's spec
    dimensions (e.g. 50×70mm for Canada).
  * `create_back_print_sheet` – a 4×6" sheet ganged 2×2 to match the
    Canadian front sheet, so each guarantor card aligns 1-to-1 with a
    photo when the prints are stacked back-to-back.
"""

from __future__ import annotations

from datetime import date
from PIL import Image, ImageDraw, ImageFont

from config.constants import (
    DEFAULT_DPI,
    PRINT_SHEET_WIDTH_IN,
    PRINT_SHEET_HEIGHT_IN,
    PRINT_SHEET_MARGIN_MM,
)
from processing.crop_resize import mm_to_px


def _load_font(size_px: int, *, italic: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a TrueType font with reasonable cross-platform fallbacks."""
    candidates: list[str] = []
    if italic and bold:
        candidates += ["arialbi.ttf", "Arial-BoldItalic.ttf", "DejaVuSans-BoldOblique.ttf"]
    elif italic:
        candidates += ["ariali.ttf", "Arial-Italic.ttf", "DejaVuSans-Oblique.ttf"]
    elif bold:
        candidates += ["arialbd.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf"]
    else:
        candidates += ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size_px)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_centered_text(draw, text, y, sheet_w, font, fill=(0, 0, 0)):
    """Helper: draw `text` centered horizontally at the given Y."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((sheet_w - text_w) // 2, y), text, font=font, fill=fill)


def create_back_template(
    width_mm: int,
    height_mm: int,
    dpi: int = DEFAULT_DPI,
    photo_date: date | None = None,
) -> Image.Image:
    """Render a single guarantor back panel at the spec dimensions.

    Args:
        width_mm:   Target width in millimetres (e.g. 50).
        height_mm:  Target height in millimetres (e.g. 70).
        dpi:        Output DPI for the rendered template.
        photo_date: Date the photo was taken (defaults to today). The
                    date is formatted DD/MM/YYYY per the user's request.

    Returns:
        PIL RGB image at the specified DPI.
    """
    if photo_date is None:
        photo_date = date.today()
    date_str = photo_date.strftime("%d/%m/%Y")

    w = mm_to_px(width_mm, dpi)
    h = mm_to_px(height_mm, dpi)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Font sizes scale with DPI so the same template renders identically
    # at preview (350 DPI) and print (350 DPI) resolutions.
    base = max(1, dpi // 32)              # ~11 px at 350 DPI
    f_brand = _load_font(int(base * 1.55), bold=True)
    f_body = _load_font(int(base * 1.05))
    f_small = _load_font(int(base * 0.85))
    f_certify = _load_font(int(base * 1.20), italic=True)

    margin_x = mm_to_px(3, dpi)
    line_h = int(base * 1.6)
    y = mm_to_px(3, dpi)

    # ── Brand block (top-left) ─────────────────────────────────────
    draw.text((margin_x, y), "VisagePass", font=f_brand, fill=(0, 0, 0))
    y += int(line_h * 1.4)
    draw.text((margin_x, y), "Digital Passport Photos", font=f_body, fill=(50, 50, 50))
    y += line_h
    draw.text((margin_x, y), "visagepass.com", font=f_small, fill=(80, 80, 80))
    y += int(line_h * 1.6)

    # ── "Photo taken — DD/MM/YYYY" ────────────────────────────────
    label = "Photo taken"
    draw.text((margin_x, y), label, font=f_body, fill=(0, 0, 0))
    label_w = draw.textbbox((0, 0), label, font=f_body)[2]
    line_x_start = margin_x + label_w + mm_to_px(2, dpi)
    line_x_end = w - margin_x
    line_y = y + int(line_h * 0.85)
    draw.line(
        [(line_x_start, line_y), (line_x_end, line_y)],
        fill=(0, 0, 0), width=max(1, dpi // 250),
    )
    # Date sits on top of the line, right-aligned
    date_bbox = draw.textbbox((0, 0), date_str, font=f_body)
    date_w = date_bbox[2] - date_bbox[0]
    draw.text(
        (line_x_end - date_w - mm_to_px(1, dpi), y),
        date_str, font=f_body, fill=(0, 0, 0),
    )
    y += int(line_h * 1.3)
    # "Date" label under the right end
    date_lbl = "Date (DD/MM/YYYY)"
    lbl_w = draw.textbbox((0, 0), date_lbl, font=f_small)[2]
    draw.text(
        (line_x_end - lbl_w, y),
        date_lbl, font=f_small, fill=(80, 80, 80),
    )
    y += int(line_h * 2.0)

    # ── Certification block (centered, italic) ────────────────────
    _draw_centered_text(draw, "I certify this to be a", y, w, f_certify)
    y += int(line_h * 1.3)
    _draw_centered_text(draw, "true likeness of", y, w, f_certify)
    y += int(line_h * 1.7)

    # Applicant name line
    name_line_y = y + int(line_h * 0.6)
    draw.line(
        [(margin_x + mm_to_px(3, dpi), name_line_y),
         (w - margin_x - mm_to_px(3, dpi), name_line_y)],
        fill=(0, 0, 0), width=max(1, dpi // 250),
    )
    y += int(line_h * 1.3)
    _draw_centered_text(draw, "(applicant's name)", y, w, f_small, fill=(80, 80, 80))

    # ── Guarantor signature (anchored to bottom) ──────────────────
    sig_label = "Guarantor's Signature"
    sig_lbl_h = draw.textbbox((0, 0), sig_label, font=f_body)[3]
    sig_label_y = h - mm_to_px(5, dpi) - sig_lbl_h
    sig_line_y = sig_label_y - int(line_h * 0.6)
    draw.line(
        [(margin_x + mm_to_px(3, dpi), sig_line_y),
         (w - margin_x - mm_to_px(3, dpi), sig_line_y)],
        fill=(0, 0, 0), width=max(1, dpi // 250),
    )
    _draw_centered_text(draw, sig_label, sig_label_y, w, f_body)

    img.info["dpi"] = (dpi, dpi)
    return img


def create_back_print_sheet(
    width_mm: int,
    height_mm: int,
    dpi: int = DEFAULT_DPI,
    orientation: str = "portrait",
    cols: int = 2,
    rows: int = 2,
    separator_mm: float | None = 0.3,
    y_offset_mm: float = 4.0,
    photo_date: date | None = None,
) -> Image.Image:
    """Render a 4×6" sheet of guarantor backs ganged to match the front sheet.

    The grid (cols, rows, separator, y_offset) MUST mirror the front
    print sheet so each back lines up with its corresponding photo when
    the two prints are stacked back-to-back.
    """
    back = create_back_template(width_mm, height_mm, dpi=dpi, photo_date=photo_date)

    if orientation == "portrait":
        sheet_w = int(PRINT_SHEET_HEIGHT_IN * dpi)
        sheet_h = int(PRINT_SHEET_WIDTH_IN * dpi)
    else:
        sheet_w = int(PRINT_SHEET_WIDTH_IN * dpi)
        sheet_h = int(PRINT_SHEET_HEIGHT_IN * dpi)

    margin = mm_to_px(PRINT_SHEET_MARGIN_MM, dpi)
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))

    photo_w, photo_h = back.size
    avail_w = sheet_w - 2 * margin - (cols - 1) * margin
    avail_h = sheet_h - 2 * margin - (rows - 1) * margin
    max_w = avail_w // cols
    max_h = avail_h // rows
    if photo_w > max_w or photo_h > max_h:
        scale = min(max_w / photo_w, max_h / photo_h)
        photo_w = int(photo_w * scale)
        photo_h = int(photo_h * scale)
        back = back.resize((photo_w, photo_h), Image.LANCZOS)

    total_w = cols * photo_w + (cols - 1) * margin
    total_h = rows * photo_h + (rows - 1) * margin
    start_x = max(margin, (sheet_w - total_w) // 2)
    y_offset_px = mm_to_px(y_offset_mm, dpi) if y_offset_mm else 0
    start_y = max(
        margin,
        min((sheet_h - total_h) // 2 + y_offset_px, sheet_h - total_h - margin),
    )

    positions: list[tuple[int, int]] = []
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (photo_w + margin)
            y = start_y + r * (photo_h + margin)
            sheet.paste(back, (x, y))
            positions.append((x, y))

    # Mirror the cut-line treatment of the front sheet so the two
    # prints register identically.
    draw = ImageDraw.Draw(sheet)
    line_color = (180, 180, 180)
    if separator_mm is not None and separator_mm > 0:
        lw = max(1, int(round(mm_to_px(separator_mm, dpi))))
    else:
        lw = max(1, dpi // 175)
    grid_w = cols * photo_w + (cols - 1) * margin
    grid_h = rows * photo_h + (rows - 1) * margin
    for c in range(1, cols):
        x = start_x + c * photo_w + (c - 1) * margin + margin // 2
        draw.line([(x, start_y), (x, start_y + grid_h)], fill=line_color, width=lw)
    for r in range(1, rows):
        y = start_y + r * photo_h + (r - 1) * margin + margin // 2
        draw.line([(start_x, y), (start_x + grid_w, y)], fill=line_color, width=lw)

    sheet.info["dpi"] = (dpi, dpi)
    return sheet
