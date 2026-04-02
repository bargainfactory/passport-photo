"""Responsive CSS styles for the passport photo editor."""

import streamlit as st

CUSTOM_CSS = """
<style>
/* ===== Global Styles ===== */
.main .block-container {
    max-width: 1200px;
    padding: 1rem 2rem;
}

h1 {
    color: #1E293B;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

h2, h3 {
    color: #334155;
    font-weight: 600;
}

/* ===== Step Progress Bar ===== */
.step-indicator {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin: 1rem 0 2rem 0;
    flex-wrap: wrap;
}

.step-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    font-size: 0.85rem;
    font-weight: 500;
    white-space: nowrap;
}

.step-active {
    background: #2563EB;
    color: white;
}

.step-completed {
    background: #16A34A;
    color: white;
}

.step-pending {
    background: #E2E8F0;
    color: #64748B;
}

/* ===== Tip Card ===== */
.tip-card {
    background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
    border-left: 4px solid #F59E0B;
    border-radius: 0.5rem;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    line-height: 1.6;
    color: #92400E;
}

.tip-card strong {
    color: #78350F;
}

/* ===== Photo Preview ===== */
.photo-container {
    border: 2px solid #E2E8F0;
    border-radius: 0.75rem;
    padding: 0.75rem;
    background: #F8FAFC;
    text-align: center;
}

.photo-container img {
    border-radius: 0.5rem;
    max-width: 100%;
    height: auto;
}

/* ===== Validation Checklist ===== */
.check-pass {
    color: #16A34A;
    font-weight: 500;
    padding: 0.25rem 0;
}

.check-fail {
    color: #DC2626;
    font-weight: 500;
    padding: 0.25rem 0;
}

/* ===== Spec Info Box ===== */
.spec-box {
    background: #F0F9FF;
    border: 1px solid #BAE6FD;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
}

.spec-box strong {
    color: #0369A1;
}

/* ===== Buttons ===== */
.stButton > button {
    border-radius: 0.5rem;
    font-weight: 600;
    padding: 0.6rem 2rem;
    transition: all 0.2s;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* ===== Download Section ===== */
.download-section {
    background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
    border: 1px solid #86EFAC;
    border-radius: 0.75rem;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
}

/* ===== Payment Card ===== */
.payment-card {
    background: white;
    border: 2px solid #E2E8F0;
    border-radius: 0.75rem;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.price-tag {
    font-size: 2rem;
    font-weight: 700;
    color: #2563EB;
    margin: 0.5rem 0;
}

/* ===== Mobile Responsive (<768px) ===== */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem 1rem;
    }

    h1 {
        font-size: 1.4rem;
    }

    h2 {
        font-size: 1.1rem;
    }

    .step-indicator {
        gap: 0.25rem;
    }

    .step-item {
        padding: 0.35rem 0.6rem;
        font-size: 0.75rem;
    }

    .stButton > button {
        width: 100%;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }

    /* Make camera input full width on mobile */
    .stCameraInput > div {
        width: 100% !important;
    }

    .price-tag {
        font-size: 1.5rem;
    }

    .tip-card {
        font-size: 0.82rem;
        padding: 0.75rem 1rem;
    }
}

/* ===== Tablet (768px - 1024px) ===== */
@media (min-width: 769px) and (max-width: 1024px) {
    .main .block-container {
        padding: 1rem 1.5rem;
    }

    h1 {
        font-size: 1.6rem;
    }
}

/* ===== Large screens (>1024px) ===== */
@media (min-width: 1025px) {
    .main .block-container {
        max-width: 1200px;
    }
}

/* ===== Footer ===== */
.app-footer {
    text-align: center;
    color: #94A3B8;
    font-size: 0.8rem;
    padding: 2rem 0 1rem 0;
    border-top: 1px solid #E2E8F0;
    margin-top: 2rem;
}
</style>
"""


def inject_css():
    """Inject the responsive CSS into the Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_step_indicator(current_step):
    """Render a horizontal step progress indicator.

    Args:
        current_step: Integer 0-3 indicating the current step
    """
    steps = [
        ("1", "Upload Photo"),
        ("2", "Select Country"),
        ("3", "Preview & Edit"),
        ("4", "Download"),
    ]

    html_parts = ['<div class="step-indicator">']
    for i, (num, label) in enumerate(steps):
        if i < current_step:
            css_class = "step-completed"
            icon = "\u2713"
        elif i == current_step:
            css_class = "step-active"
            icon = num
        else:
            css_class = "step-pending"
            icon = num

        html_parts.append(
            f'<div class="step-item {css_class}">'
            f"<span>{icon}</span> {label}</div>"
        )
    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)
