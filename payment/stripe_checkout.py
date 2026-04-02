"""Stripe Checkout integration for payment processing.

Uses Stripe Checkout Sessions for a redirect-based payment flow.
Supports multiple currencies with automatic conversion.
"""

import os
import streamlit as st

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from config.constants import PHOTO_PRICE_CENTS


def _get_stripe_key():
    """Get the Stripe secret key from environment or Streamlit secrets."""
    # Try Streamlit secrets first
    try:
        return st.secrets["STRIPE_SECRET_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    # Fall back to environment variable
    return os.environ.get("STRIPE_SECRET_KEY", "")


def is_stripe_configured():
    """Check if Stripe is properly configured with an API key."""
    if not STRIPE_AVAILABLE:
        return False
    key = _get_stripe_key()
    return bool(key) and key != "sk_test_your_key_here"


def create_checkout_session(currency="usd", price_cents=None):
    """Create a Stripe Checkout Session and return the checkout URL.

    Args:
        currency: Lowercase currency code (e.g., "usd", "eur", "inr")
        price_cents: Override price in cents (default from constants)

    Returns:
        Checkout URL string, or None on failure
    """
    if not is_stripe_configured():
        return None

    stripe.api_key = _get_stripe_key()
    amount = price_cents or PHOTO_PRICE_CENTS

    # Build success/cancel URLs
    # In Streamlit, we use query params to detect return from Stripe
    base_url = _get_app_url()
    success_url = f"{base_url}?paid=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}?cancelled=true"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": "Passport/Visa Photo Download",
                        "description": "Compliant passport or visa photo - digital download",
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    except stripe.error.StripeError as e:
        st.error(f"Payment error: {e.user_message or str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected payment error: {str(e)}")
        return None


def verify_payment(session_id):
    """Verify that a Stripe Checkout Session was paid.

    Args:
        session_id: The Stripe Checkout Session ID from the return URL

    Returns:
        True if payment was successful, False otherwise
    """
    if not is_stripe_configured():
        return False

    stripe.api_key = _get_stripe_key()

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"
    except Exception:
        return False


def _get_app_url():
    """Get the current app URL for Stripe redirects.

    In Streamlit Cloud, this is the deployed URL.
    Locally, defaults to localhost.
    """
    # Try to detect from Streamlit config/environment
    try:
        # Streamlit Cloud sets this
        url = st.secrets.get("APP_URL", "")
        if url:
            return url.rstrip("/")
    except (FileNotFoundError, AttributeError):
        pass

    # Fallback to localhost for development
    return "http://localhost:8501"
