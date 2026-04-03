"""SEO meta tags, OpenGraph, Twitter Card, and JSON-LD schema injection."""

import streamlit as st
import json


def inject_meta_tags():
    """Inject HTML meta, OpenGraph, Twitter Card, and JSON-LD into the page."""

    title = "Instant Passport and Visa Photo Maker - Compliant for 50+ Countries"
    description = (
        "Create perfect digital passport and visa photos online for USA, Saudi Arabia, "
        "UAE, India, China, EU, and more. Upload selfie, auto-edit, compliant download."
    )
    keywords = (
        "passport photo online, visa photo editor, biometric passport photo, "
        "ID photo maker, passport photo app, passport photo generator, visa photo tool"
    )
    site_url = "https://passport-photo-editor.streamlit.app"

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Passport and Visa Photo Editor",
        "description": description,
        "url": site_url,
        "applicationCategory": "PhotographyApplication",
        "operatingSystem": "Any",
        "offers": {
            "@type": "Offer",
            "price": "4.99",
            "priceCurrency": "USD",
        },
        "featureList": [
            "Passport photo for 50+ countries",
            "AI background removal",
            "Automatic face detection and cropping",
            "Webcam selfie support",
            "Print-ready 4x6 sheets at 300 DPI",
        ],
    })

    meta_html = (
        f'<meta name="description" content="{description}">'
        f'<meta name="keywords" content="{keywords}">'
        f'<meta name="robots" content="index, follow">'
        f'<meta property="og:type" content="website">'
        f'<meta property="og:title" content="{title}">'
        f'<meta property="og:description" content="{description}">'
        f'<meta name="twitter:card" content="summary">'
        f'<meta name="twitter:title" content="{title}">'
        f'<meta name="twitter:description" content="{description}">'
        f'<script type="application/ld+json">{json_ld}</script>'
    )

    st.markdown(meta_html, unsafe_allow_html=True)
