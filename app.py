"""Passport & Visa Photo Editor - Main Application Entry Point.

A Streamlit web application that transforms uploaded photos or webcam selfies
into compliant passport and visa photos for 50+ countries worldwide.

Flow: Country Selection -> Upload Photo -> Preview & Validate -> Download

Run with: streamlit run app.py
"""

import streamlit as st
from config.seo import inject_meta_tags
from ui.styles import inject_css, render_step_indicator
from ui import step_configure, step_upload, step_preview, step_download

# Page Config (must be first Streamlit command)
st.set_page_config(
    page_title="Passport & Visa Photo Editor",
    page_icon=":camera:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# SEO Meta Tags
inject_meta_tags()

# Custom CSS
inject_css()

# Initialize Session State
if "step" not in st.session_state:
    st.session_state["step"] = 0
if "paid" not in st.session_state:
    st.session_state["paid"] = False

# App Header
st.markdown(
    """<div class="app-header">
        <div class="header-icon">&#9878;</div>
        <h1 class="header-title">Passport &amp; Visa Photo Editor</h1>
        <p class="header-subtitle">
            Professional passport and visa photos for 50+ countries.
            Upload once, get compliant, print-ready results in seconds.
        </p>
        <div class="header-badges">
            <span class="badge"><span class="badge-icon">&#127760;</span> 34 Countries</span>
            <span class="badge"><span class="badge-icon">&#9881;</span> AI Processing</span>
            <span class="badge"><span class="badge-icon">&#128438;</span> 300 DPI Output</span>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# Step Progress Indicator
current_step = st.session_state["step"]
render_step_indicator(current_step)

# Step Router
if current_step == 0:
    step_configure.render()
elif current_step == 1:
    step_upload.render()
elif current_step == 2:
    step_preview.render()
elif current_step == 3:
    step_download.render()

# Footer
st.markdown("---")
st.markdown(
    """<div class="app-footer">
        <p><span class="footer-brand">&#9878; Passport &amp; Visa Photo Editor</span></p>
        <p>50+ countries &middot; 300 DPI print-ready &middot; AI-powered processing</p>
        <p style="font-size:0.75rem;color:#94A3B8;margin-top:0.5rem;">
        &#128274; Photos are processed locally and never stored on any server.
        &copy; 2026 Passport Photo Editor. All rights reserved.</p>
    </div>""",
    unsafe_allow_html=True,
)
