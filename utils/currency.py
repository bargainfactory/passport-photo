"""Country-to-currency mapping and exchange-rate conversion for Stripe.

Fetches live USD-based exchange rates from the Open Exchange Rates API
and caches them for one hour. Falls back to USD if the target currency
is unsupported or if the rate fetch fails.
"""

import time
import urllib.request
import json
import logging

logger = logging.getLogger(__name__)

COUNTRY_CURRENCY: dict[str, str] = {
    "United States": "usd",
    "Canada": "cad",
    "Brazil": "brl",
    "Mexico": "mxn",
    "United Kingdom": "gbp",
    "Schengen / EU": "eur",
    "Germany": "eur",
    "France": "eur",
    "Russia": "rub",
    "Turkey": "try",
    "Australia": "aud",
    "New Zealand": "nzd",
    "India": "inr",
    "China": "cny",
    "Japan": "jpy",
    "South Korea": "krw",
    "Thailand": "thb",
    "Philippines": "php",
    "Indonesia": "idr",
    "Vietnam": "vnd",
    "Malaysia": "myr",
    "Singapore": "sgd",
    "Hong Kong": "hkd",
    "Pakistan": "pkr",
    "Saudi Arabia": "sar",
    "United Arab Emirates": "aed",
    "Egypt": "egp",
    "Qatar": "qar",
    "Jordan": "jod",
    "Iran": "irr",
    "Israel": "ils",
    "South Africa": "zar",
    "Nigeria": "ngn",
    "Kenya": "kes",
}

ZERO_DECIMAL_CURRENCIES = {
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga",
    "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf",
}

STRIPE_UNSUPPORTED = {"irr"}

_rate_cache: dict[str, float] = {}
_rate_cache_time: float = 0
_CACHE_TTL = 3600  # 1 hour


def _fetch_rates() -> dict[str, float]:
    """Fetch current USD-based exchange rates."""
    global _rate_cache, _rate_cache_time

    if _rate_cache and (time.time() - _rate_cache_time) < _CACHE_TTL:
        return _rate_cache

    try:
        req = urllib.request.Request(
            "https://open.er-api.com/v6/latest/USD",
            headers={"User-Agent": "VisagePass/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        if data.get("result") == "success":
            _rate_cache = {k.lower(): v for k, v in data["rates"].items()}
            _rate_cache_time = time.time()
            return _rate_cache
    except Exception as e:
        logger.warning("Exchange rate fetch failed: %s", e)

    return _rate_cache


def get_currency_for_country(country_name: str) -> str:
    currency = COUNTRY_CURRENCY.get(country_name, "usd")
    if currency in STRIPE_UNSUPPORTED:
        return "usd"
    return currency


def convert_usd_cents(usd_cents: int, target_currency: str) -> int:
    """Convert a USD amount (in cents) to the target currency's smallest unit.

    For standard currencies, returns the amount in cents/pence/etc.
    For zero-decimal currencies (JPY, KRW, VND...), returns the whole-unit amount.
    """
    if target_currency == "usd":
        return usd_cents

    rates = _fetch_rates()
    rate = rates.get(target_currency)
    if rate is None:
        return usd_cents

    usd_amount = usd_cents / 100
    local_amount = usd_amount * rate

    if target_currency in ZERO_DECIMAL_CURRENCIES:
        return round(local_amount)

    return round(local_amount * 100)


def get_localized_pricing(
    country_name: str, items_prices_usd: dict[str, int],
) -> dict:
    """Return pricing info for a country.

    Args:
        country_name: Country name from the frontend.
        items_prices_usd: Mapping of item key → price in USD cents,
            e.g. {"digital": 499, "sheet": 499, "bundle": 899}.

    Returns:
        Dict with currency code, prices per item, and exchange rate.
    """
    currency = get_currency_for_country(country_name)
    rates = _fetch_rates()
    rate = rates.get(currency, 1.0) if currency != "usd" else 1.0

    prices = {}
    for item, usd_cents in items_prices_usd.items():
        prices[item] = convert_usd_cents(usd_cents, currency)

    return {
        "currency": currency,
        "rate": rate,
        "prices": prices,
        "zero_decimal": currency in ZERO_DECIMAL_CURRENCIES,
    }
