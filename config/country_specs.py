"""Passport and visa photo specifications for 30+ countries.

Each entry defines the required photo dimensions, background color,
head size proportions, and compliance rules per country/document type.

Specifications sourced from official government photo requirements.
All sizes in millimeters, output at 300 DPI.
"""

# Country flag emoji lookup for UI display
COUNTRY_FLAGS = {
    "United States": "🇺🇸",
    "Canada": "🇨🇦",
    "United Kingdom": "🇬🇧",
    "Australia": "🇦🇺",
    "India": "🇮🇳",
    "China": "🇨🇳",
    "Schengen / EU": "🇪🇺",
    "Japan": "🇯🇵",
    "Brazil": "🇧🇷",
    "Russia": "🇷🇺",
    "South Africa": "🇿🇦",
    "Mexico": "🇲🇽",
    "Saudi Arabia": "🇸🇦",
    "United Arab Emirates": "🇦🇪",
    "Egypt": "🇪🇬",
    "Qatar": "🇶🇦",
    "Jordan": "🇯🇴",
    "South Korea": "🇰🇷",
    "Thailand": "🇹🇭",
    "Philippines": "🇵🇭",
    "Indonesia": "🇮🇩",
    "Pakistan": "🇵🇰",
    "Vietnam": "🇻🇳",
    "Malaysia": "🇲🇾",
    "Singapore": "🇸🇬",
    "Hong Kong": "🇭🇰",
    "Turkey": "🇹🇷",
    "Iran": "🇮🇷",
    "Israel": "🇮🇱",
    "New Zealand": "🇳🇿",
    "Germany": "🇩🇪",
    "France": "🇫🇷",
    "Nigeria": "🇳🇬",
    "Kenya": "🇰🇪",
    "Other / Custom": "🌍",
}


COUNTRY_SPECS = {
    # ── Americas ──
    "United States": {
        "passport": {
            "width_mm": 51, "height_mm": 51,  # 2x2 inches
            "bg_color": (255, 255, 255),
            # Head height ≈ 1.34" (34.2mm = 67% of the 2" frame), with
            # 3mm crown clearance at the top.
            "head_pct": (67, 67),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 3,
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,
            "bg_color": (255, 255, 255),
            "head_pct": (67, 67),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 3,
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open, mouth closed",
        "notes": "No glasses since 2016. No headgear except religious. White background only.",
    },
    "Canada": {
        # Head 35-36mm on a 70mm-tall photo → head_pct ≈ 50-51% of height.
        "passport": {
            "width_mm": 50, "height_mm": 70,
            "bg_color": (255, 255, 255),
            "head_pct": (50, 51),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 10,
            "print_sheet": {
                "orientation": "portrait",
                "cols": 2, "rows": 2,
                "separator_mm": 0.3,
                "y_offset_mm": 4,
            },
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 10,
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed, eyes open",
        "notes": "Head 35-36mm on 50x70mm photo. White or light-colored background.",
    },
    "Brazil": {
        "passport": {
            "width_mm": 50, "height_mm": 70,
            "bg_color": (255, 255, 255),
            "head_pct": (60, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,
            "bg_color": (255, 255, 255),
            "head_pct": (60, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed",
        "notes": "White background. No glasses.",
    },
    "Mexico": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, no smile",
        "notes": "White background. No glasses.",
    },

    # ── Europe ──
    "United Kingdom": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (67, 67),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 3,
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (67, 67),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 3,
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed, no smile",
        "notes": "No glasses. Light grey background also accepted.",
    },
    "Schengen / EU": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (67, 67),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 3,
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (67, 67),
            "eye_line_pct": (56, 69),
            "crown_top_mm": 3,
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, mouth closed",
        "notes": (
            "Applies to all Schengen Area countries: Austria, Belgium, Czech Republic, "
            "Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Italy, "
            "Latvia, Lithuania, Luxembourg, Malta, Netherlands, Norway, Poland, Portugal, "
            "Slovakia, Slovenia, Spain, Sweden, Switzerland. "
            "White or light grey background. Glasses allowed if eyes clearly visible."
        ),
    },
    "Germany": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, mouth closed, eyes open",
        "notes": "White or light grey background. Follows Schengen/EU standard. Glasses allowed if no glare.",
    },
    "France": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed",
        "notes": "White or light grey/blue background. Follows Schengen/EU standard. No glasses since 2018.",
    },
    "Russia": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, mouth closed",
        "notes": "White background preferred. Glasses allowed if clear lenses, no tinted.",
    },
    "Turkey": {
        "passport": {
            "width_mm": 50, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. Glasses ok if clear lenses, no glare.",
    },

    # ── Asia-Pacific ──
    "Australia": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (64, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (64, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed",
        "notes": "No glasses. Plain white or light grey background.",
    },
    "New Zealand": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (66, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (66, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed, eyes open",
        "notes": "No glasses. White or off-white background.",
    },
    "India": {
        "passport": {
            "width_mm": 51, "height_mm": 51,  # 2x2 inches
            "bg_color": (255, 255, 255),
            "head_pct": (50, 70),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,
            "bg_color": (255, 255, 255),
            "head_pct": (50, 70),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open, mouth closed",
        "notes": "White background only. No glasses. No headgear except religious.",
    },
    "China": {
        "passport": {
            "width_mm": 33, "height_mm": 48,
            "bg_color": (255, 255, 255),
            "head_pct": (62, 73),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 33, "height_mm": 48,
            "bg_color": (255, 255, 255),
            "head_pct": (62, 73),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, no smile, eyes open",
        "notes": "White background. Head height 28-33mm. No glasses, no headgear.",
    },
    "Japan": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 45, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, mouth closed, eyes open",
        "notes": "White or light background. Glasses ok if no glare.",
    },
    "South Korea": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (71, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (71, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed",
        "notes": "White background. Head 32-36mm. No glasses preferred.",
    },
    "Thailand": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White or light background. Glasses ok if not reflective. Also accepts 2x2\" for some visas.",
    },
    "Philippines": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (71, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (71, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral (slight smile ok, no teeth showing)",
        "notes": "White or light blue background. Head 32-36mm. No glasses unless medical. No headgear.",
    },
    "Indonesia": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (60, 70),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (60, 70),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. No glasses. Religious headgear allowed.",
    },
    "Vietnam": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,  # 2x2 inches
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. No glasses, no headgear.",
    },
    "Malaysia": {
        "passport": {
            "width_mm": 35, "height_mm": 50,
            "bg_color": (255, 255, 255),
            "head_pct": (50, 60),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 50,
            "bg_color": (255, 255, 255),
            "head_pct": (50, 60),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": True,
        "expression": "Neutral, mouth closed",
        "notes": "White background. Glasses ok if clear. Dark-colored headscarf allowed.",
    },
    "Singapore": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. No glasses if possible. Religious headgear allowed.",
    },
    "Hong Kong": {
        "passport": {
            "width_mm": 40, "height_mm": 50,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 40, "height_mm": 50,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. Head 32-36mm. Religious/medical headgear allowed.",
    },
    "Pakistan": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. Glasses if eyes visible. No hats.",
    },

    # ── Middle East ──
    "Saudi Arabia": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,  # 2x2 inches
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open, mouth closed",
        "notes": (
            "White or light gray background. No glasses. "
            "No headgear except religious. Head 70-80% of frame (~28-48mm)."
        ),
    },
    "United Arab Emirates": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. Glasses if eyes clearly visible. Religious/medical headgear allowed.",
    },
    "Egypt": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. No glasses, no headgear.",
    },
    "Qatar": {
        "passport": {
            "width_mm": 38, "height_mm": 48,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White or light blue background. Glasses ok if clear.",
    },
    "Jordan": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. Glasses if eyes visible.",
    },
    "Iran": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": True,
        "expression": "Neutral, eyes open",
        "notes": "White background. No glasses. Headscarf required for women.",
    },
    "Israel": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (240, 240, 240),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (240, 240, 240),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "Light background (white or light grey). Glasses ok if no tint or glare.",
    },

    # ── Africa ──
    "South Africa": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (60, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (60, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": True,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White or light grey background.",
    },
    "Nigeria": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open, mouth closed",
        "notes": "White background. No glasses, no headgear except religious.",
    },
    "Kenya": {
        "passport": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open",
        "notes": "White background. No glasses, no headgear.",
    },
}

# "Other/Custom" is handled in the UI — user enters dimensions manually


def get_country_list():
    """Return sorted list of country names plus 'Other / Custom' at end."""
    countries = sorted(COUNTRY_SPECS.keys())
    countries.append("Other / Custom")
    return countries


def get_spec(country, doc_type="passport"):
    """Get the photo spec for a country and document type.

    Args:
        country: Country name from COUNTRY_SPECS
        doc_type: 'passport' or 'visa'

    Returns:
        dict with width_mm, height_mm, bg_color, head_pct, eye_line_pct,
        plus top-level glasses/headgear/expression/notes fields.
    """
    if country not in COUNTRY_SPECS:
        return None
    entry = COUNTRY_SPECS[country]
    doc_key = doc_type.lower()
    if doc_key not in entry:
        doc_key = "passport"  # fallback

    spec = dict(entry[doc_key])
    spec["glasses"] = entry.get("glasses", False)
    spec["headgear"] = entry.get("headgear", False)
    spec["expression"] = entry.get("expression", "Neutral")
    spec["notes"] = entry.get("notes", "")
    return spec
