"""App-wide constants: pricing, DPI, currency mappings."""

# Default output DPI for all passport/visa photos
DEFAULT_DPI = 300

# Stripe payment amount in cents (USD base)
PHOTO_PRICE_CENTS = 499  # $4.99
PHOTO_PRICE_DISPLAY = "$4.99"

# Print sheet dimensions (4x6 inches at 300 DPI)
PRINT_SHEET_WIDTH_IN = 6
PRINT_SHEET_HEIGHT_IN = 4
PRINT_SHEET_MARGIN_MM = 2

# Supported output formats
OUTPUT_FORMATS = ["JPEG", "PNG"]

# Maximum upload size in MB
MAX_UPLOAD_MB = 10

# Minimum acceptable image resolution
MIN_IMAGE_WIDTH = 600
MIN_IMAGE_HEIGHT = 600

# Face detection thresholds
FACE_SCALE_FACTOR = 1.1
FACE_MIN_NEIGHBORS = 5
FACE_MIN_SIZE = (100, 100)

# Tilt threshold in degrees
MAX_TILT_DEGREES = 15

# Country code to currency mapping for geo-IP based currency detection
COUNTRY_CURRENCY_MAP = {
    "US": "usd", "CA": "cad", "GB": "gbp", "AU": "aud",
    "IN": "inr", "CN": "cny", "JP": "jpy", "KR": "krw",
    "BR": "brl", "MX": "mxn", "RU": "rub", "ZA": "zar",
    "AE": "aed", "SA": "sar", "EG": "egp", "QA": "qar",
    "JO": "jod", "TH": "thb", "PH": "php", "ID": "idr",
    "PK": "pkr", "VN": "vnd", "MY": "myr", "SG": "sgd",
    "HK": "hkd", "TR": "try", "IR": "irr", "IL": "ils",
    "EU": "eur", "DE": "eur", "FR": "eur", "IT": "eur",
    "ES": "eur", "NL": "eur", "BE": "eur", "AT": "eur",
    "PT": "eur", "GR": "eur", "IE": "eur", "FI": "eur",
    "SE": "sek", "NO": "nok", "DK": "dkk", "PL": "pln",
    "CZ": "czk", "CH": "chf", "NZ": "nzd",
}

# Currencies supported by Stripe for display
SUPPORTED_CURRENCIES = [
    ("USD", "$", "US Dollar"),
    ("EUR", "\u20ac", "Euro"),
    ("GBP", "\u00a3", "British Pound"),
    ("CAD", "C$", "Canadian Dollar"),
    ("AUD", "A$", "Australian Dollar"),
    ("INR", "\u20b9", "Indian Rupee"),
    ("AED", "AED", "UAE Dirham"),
    ("SAR", "SAR", "Saudi Riyal"),
    ("JPY", "\u00a5", "Japanese Yen"),
    ("KRW", "\u20a9", "Korean Won"),
    ("SGD", "S$", "Singapore Dollar"),
    ("MYR", "RM", "Malaysian Ringgit"),
    ("THB", "\u0e3f", "Thai Baht"),
    ("PHP", "\u20b1", "Philippine Peso"),
    ("BRL", "R$", "Brazilian Real"),
    ("MXN", "MX$", "Mexican Peso"),
    ("TRY", "\u20ba", "Turkish Lira"),
    ("ZAR", "R", "South African Rand"),
]

# Currency symbol lookup
CURRENCY_SYMBOLS = {code: symbol for code, symbol, _ in SUPPORTED_CURRENCIES}
