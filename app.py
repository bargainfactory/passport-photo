"""Passport & Visa Photo Editor - Main Application Entry Point.

A Streamlit web application that transforms uploaded photos or webcam selfies
into compliant passport and visa photos for 50+ countries worldwide.

Run with: streamlit run app.py
"""

import streamlit as st
from config.seo import inject_meta_tags
from ui.styles import inject_css, render_step_indicator
from ui import step_upload, step_configure, step_preview, step_download

# ── Page Config (must be first Streamlit command) ──
st.set_page_config(
    page_title="Passport & Visa Photo Editor \u2013 Worldwide Compliant Photos",
    page_icon="\ud83d\udcf7",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": (
            "# Passport & Visa Photo Editor\n"
            "Create compliant passport and visa photos for 50+ countries.\n\n"
            "Upload a photo or take a selfie, select your country, and get a "
            "print-ready photo in seconds."
        ),
    },
)

# ── SEO Meta Tags ──
inject_meta_tags()

# ── Custom CSS ──
inject_css()

# ── Initialize Session State ──
if "step" not in st.session_state:
    st.session_state["step"] = 0
if "paid" not in st.session_state:
    st.session_state["paid"] = False

# ── App Header ──
st.markdown(
    "<h1 style='text-align:center;'>"
    "\ud83d\udcf7 Passport & Visa Photo Editor"
    "</h1>"
    "<p style='text-align:center; color:#64748B; margin-bottom:1.5rem;'>"
    "Create compliant passport and visa photos for 50+ countries. "
    "Upload a selfie, auto-edit, and download print-ready photos."
    "</p>",
    unsafe_allow_html=True,
)

# ── Step Progress Indicator ──
current_step = st.session_state["step"]
render_step_indicator(current_step)

# ── Step Router ──
if current_step == 0:
    step_upload.render()
elif current_step == 1:
    step_configure.render()
elif current_step == 2:
    step_preview.render()
elif current_step == 3:
    step_download.render()

# ── Footer ──
st.markdown(
    '<div class="app-footer">'
    "Passport & Visa Photo Editor &middot; Compliant photos for 50+ countries<br>"
    "Photos are processed locally and not stored on any server.<br>"
    "&copy; 2026 Passport Photo Editor. All rights reserved."
    "</div>",
    unsafe_allow_html=True,
)
