"""Geo-IP based currency detection using free API."""

import streamlit as st
import requests
from config.constants import COUNTRY_CURRENCY_MAP


@st.cache_data(ttl=3600)
def detect_currency():
    """Detect the user's likely currency based on their IP geolocation.

    Uses ip-api.com (free, no key required, 45 req/min limit).
    Falls back to USD on any error.

    Returns:
        Currency code string (lowercase), e.g. "usd", "eur", "inr"
    """
    try:
        resp = requests.get("http://ip-api.com/json/?fields=countryCode", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            country_code = data.get("countryCode", "US")
            return COUNTRY_CURRENCY_MAP.get(country_code, "usd")
    except (requests.RequestException, ValueError, KeyError):
        pass
    return "usd"


def get_currency_display(currency_code):
    """Get a display-friendly currency string.

    Args:
        currency_code: Lowercase currency code, e.g. "usd"

    Returns:
        Uppercase code, e.g. "USD"
    """
    return currency_code.upper()
