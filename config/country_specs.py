"""Passport and visa photo specifications for 30+ countries.

Each entry defines the required photo dimensions, background color,
head size proportions, and compliance rules per country/document type.
"""

COUNTRY_SPECS = {
    "United States": {
        "passport": {
            "width_mm": 51, "height_mm": 51,
            "bg_color": (255, 255, 255),
            "head_pct": (50, 69),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,
            "bg_color": (255, 255, 255),
            "head_pct": (50, 69),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open, mouth closed",
        "notes": "No glasses since 2016. No headgear except religious.",
    },
    "Canada": {
        "passport": {
            "width_mm": 50, "height_mm": 70,
            "bg_color": (255, 255, 255),
            "head_pct": (31, 36),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 35, "height_mm": 45,
            "bg_color": (255, 255, 255),
            "head_pct": (31, 36),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, mouth closed, eyes open",
        "notes": "No glasses. Head 31-36mm in height.",
    },
    "United Kingdom": {
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
        "expression": "Neutral, mouth closed, no smile",
        "notes": "No glasses. Light grey background also accepted.",
    },
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
    "India": {
        "passport": {
            "width_mm": 51, "height_mm": 51,
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
        "notes": "White background only. No glasses.",
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
        "notes": "White background. Head height 28-33mm. No glasses.",
    },
    "Schengen / EU": {
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
        "notes": "Light grey or white background. Glasses allowed if eyes clearly visible.",
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
        "notes": "White background preferred. Glasses allowed if clear lenses.",
    },
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
    "Saudi Arabia": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "glasses": False,
        "headgear": False,
        "expression": "Neutral, eyes open, mouth closed",
        "notes": "White or light gray background. No glasses. No headgear except religious.",
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
        "notes": "White background. Glasses if eyes clearly visible. Religious headgear allowed.",
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
        "notes": "White or light background. Glasses ok if not reflective.",
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
        "notes": "White or light blue background. Head 32-36mm. No glasses unless medical.",
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
        "notes": "White background. Religious headgear allowed.",
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
    "Vietnam": {
        "passport": {
            "width_mm": 40, "height_mm": 60,
            "bg_color": (255, 255, 255),
            "head_pct": (70, 80),
            "eye_line_pct": (56, 69),
        },
        "visa": {
            "width_mm": 51, "height_mm": 51,
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
        "notes": "White background. Glasses ok if clear lenses.",
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
        "notes": "Light background (white/light grey). Glasses ok.",
    },
}

# "Other/Custom" is handled in UI — user enters dimensions manually


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
