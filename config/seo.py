"""SEO meta tags, OpenGraph, and JSON-LD schema injection for Streamlit."""

import streamlit as st
import json


def inject_meta_tags():
    """Inject HTML meta, OpenGraph, Twitter Card, and JSON-LD into the page head."""

    title = "Instant Passport & Visa Photo Maker \u2013 Compliant for 50+ Countries | Free Preview"
    description = (
        "Create perfect digital passport and visa photos online for USA, Saudi Arabia, "
        "UAE, India, China, EU, and more. Upload selfie, auto-edit, compliant download. "
        "Pay in your currency."
    )
    keywords = (
        "passport photo online, visa photo editor, biometric passport photo, "
        "ID photo maker, passport photo app, passport photo generator, visa photo tool, "
        "passport size photo, online photo editor, digital passport photo, "
        "passport photo from selfie, visa photo from phone"
    )
    site_url = "https://passport-photo-editor.streamlit.app"

    # JSON-LD structured data for WebApplication
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Passport & Visa Photo Editor",
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
            "Print-ready 4x6 sheets",
            "Biometric compliance validation",
        ],
        "keywords": keywords,
    }

    meta_html = f"""
    <!-- Primary Meta Tags -->
    <meta name="title" content="{title}">
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <meta name="robots" content="index, follow">
    <meta name="language" content="English">
    <meta name="author" content="Passport Photo Editor">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{site_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:site_name" content="Passport & Visa Photo Editor">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{site_url}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">

    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {json.dumps(json_ld, indent=2)}
    </script>
    """

    st.markdown(meta_html, unsafe_allow_html=True)
