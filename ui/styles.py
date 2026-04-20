"""Corporate-tech CSS for the passport photo editor.

Emerald + slate gray + turquoise palette with professional icons
and calm animations. Fully responsive.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
/* ===== Hide Streamlit chrome ===== */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* ===== Calm keyframe animations ===== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.15); }
    50%      { box-shadow: 0 0 0 8px rgba(5, 150, 105, 0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-8px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ===== Global ===== */
.main .block-container {
    max-width: 1100px;
    padding: 0.5rem 1.5rem 2rem;
}

/* ===== App Header ===== */
.app-header {
    text-align: center;
    padding: 2.5rem 1rem 1.25rem;
    animation: fadeInUp 0.6s ease-out;
}

.header-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: linear-gradient(135deg, #059669, #0D9488);
    color: white;
    font-size: 1.6rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 4px 16px rgba(5, 150, 105, 0.25);
    animation: pulseGlow 3s ease-in-out infinite;
}

.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #059669, #0D9488, #0891B2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

.header-subtitle {
    color: #64748B;
    font-size: 1rem;
    max-width: 580px;
    margin: 0.75rem auto 1rem;
    line-height: 1.65;
}

.header-badges {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
}

.badge {
    background: #F0FDF4;
    border: 1px solid #A7F3D0;
    color: #047857;
    border-radius: 2rem;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    transition: all 0.25s ease;
}

.badge:hover {
    background: #ECFDF5;
    border-color: #6EE7B7;
    transform: translateY(-1px);
}

.badge .badge-icon {
    font-size: 0.85rem;
    opacity: 0.85;
}

/* ===== Step Progress Bar ===== */
.step-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0;
    margin: 0.5rem auto 1.75rem;
    max-width: 650px;
    animation: fadeIn 0.5s ease-out 0.2s both;
}

.step-num {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
    transition: all 0.35s ease;
}

.step-label {
    font-size: 0.78rem;
    font-weight: 600;
    margin-left: 0.35rem;
    white-space: nowrap;
    transition: color 0.3s ease;
}

.step-group {
    display: flex;
    align-items: center;
}

.step-line {
    width: 40px;
    height: 2px;
    flex-shrink: 0;
    transition: background 0.4s ease;
}

.step-done .step-num {
    background: #059669;
    color: white;
    box-shadow: 0 2px 6px rgba(5, 150, 105, 0.2);
}
.step-done .step-label { color: #059669; }
.step-done + .step-line-wrap .step-line { background: #059669; }

.step-active .step-num {
    background: linear-gradient(135deg, #059669, #0D9488);
    color: white;
    box-shadow: 0 2px 10px rgba(5, 150, 105, 0.35);
    animation: pulseGlow 2.5s ease-in-out infinite;
}
.step-active .step-label { color: #059669; }

.step-todo .step-num {
    background: #E2E8F0;
    color: #94A3B8;
}
.step-todo .step-label { color: #94A3B8; }

.step-line-wrap {
    display: flex;
    align-items: center;
}

.line-done { background: #059669; }
.line-active {
    background: linear-gradient(90deg, #059669, #0D9488);
}
.line-todo { background: #E2E8F0; }

/* ===== Section Titles ===== */
.section-label {
    text-align: center;
    color: #94A3B8;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.25rem;
}

/* ===== Tip Card ===== */
.tip-card {
    background: linear-gradient(135deg, #F0FDFA, #CCFBF1);
    border-left: 4px solid #14B8A6;
    border-radius: 0.625rem;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    line-height: 1.65;
    color: #134E4A;
    animation: fadeInUp 0.4s ease-out;
}

.tip-card b { color: #0F766E; }

.tip-card .tip-icon {
    display: inline-block;
    margin-right: 0.35rem;
    font-size: 1rem;
}

/* ===== Spec Box ===== */
.spec-box {
    background: linear-gradient(135deg, #F8FAFB, #F0FDF4);
    border: 1px solid #A7F3D0;
    border-radius: 0.625rem;
    padding: 1.15rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    line-height: 1.8;
    animation: fadeInUp 0.4s ease-out;
}

.spec-box b { color: #047857; }

.spec-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #064E3B;
    margin-bottom: 0.5rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #A7F3D0;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* ===== Country Badge ===== */
.country-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: linear-gradient(135deg, #F0FDF4, #F0FDFA);
    border: 1px solid #A7F3D0;
    border-radius: 2rem;
    padding: 0.35rem 1rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: #047857;
    margin-bottom: 0.5rem;
    transition: all 0.25s ease;
}

.country-tag:hover {
    box-shadow: 0 2px 8px rgba(5, 150, 105, 0.12);
}

/* ===== Photo Container ===== */
.photo-box {
    border: 2px solid #E2E8F0;
    border-radius: 0.75rem;
    padding: 0.5rem;
    background: #F8FAFB;
    text-align: center;
    transition: all 0.3s ease;
}

.photo-box:hover {
    border-color: #059669;
    box-shadow: 0 4px 16px rgba(5, 150, 105, 0.1);
}

.photo-box-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.4rem;
    margin-bottom: 0.2rem;
}

/* ===== Validation ===== */
.val-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 0.625rem;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    animation: fadeIn 0.4s ease-out;
}

.val-pass {
    color: #059669;
    font-weight: 500;
    padding: 0.25rem 0;
    font-size: 0.88rem;
    animation: slideIn 0.3s ease-out both;
}

.val-fail {
    color: #DC2626;
    font-weight: 500;
    padding: 0.25rem 0;
    font-size: 0.88rem;
    animation: slideIn 0.3s ease-out both;
}

.val-pass b, .val-fail b { font-weight: 700; }

/* ===== Payment Card ===== */
.pay-card {
    background: white;
    border: 2px solid #E2E8F0;
    border-radius: 0.875rem;
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    max-width: 420px;
    margin: 1rem auto;
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease-out;
}

.pay-card:hover {
    border-color: #A7F3D0;
    box-shadow: 0 8px 30px rgba(5, 150, 105, 0.1);
}

.pay-card h3 {
    color: #1E293B;
    margin: 0 0 0.5rem;
    font-weight: 700;
}

.price-big {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #059669, #0D9488);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.5rem 0;
    line-height: 1.2;
}

.pay-features {
    text-align: left;
    padding: 0.5rem 0;
    margin: 0.5rem 0;
    font-size: 0.88rem;
    color: #475569;
    line-height: 1.9;
}

.pay-features .feat-check {
    color: #059669;
    font-weight: 700;
    margin-right: 0.25rem;
}

/* ===== Download Section ===== */
.dl-section {
    background: linear-gradient(135deg, #F0FDF4, #ECFDF5);
    border: 1px solid #A7F3D0;
    border-radius: 0.75rem;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
    animation: fadeInUp 0.5s ease-out;
}

.dl-section h3 {
    color: #064E3B;
    margin: 0 0 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
}

.dl-section p { color: #047857; font-size: 0.9rem; }

/* ===== Email Card ===== */
.email-card {
    background: linear-gradient(135deg, #F0FDFA, #F0FDF4);
    border: 1px solid #99F6E4;
    border-radius: 0.625rem;
    padding: 0.75rem 1rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    animation: fadeIn 0.4s ease-out;
}

/* ===== Buttons ===== */
.stButton > button {
    border-radius: 0.5rem;
    font-weight: 600;
    padding: 0.6rem 2rem;
    transition: all 0.3s ease;
    position: relative;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(5, 150, 105, 0.25);
}

.stButton > button:active {
    transform: translateY(0);
}

/* ===== Footer ===== */
.app-footer {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    color: #64748B;
    font-size: 0.82rem;
    line-height: 1.5;
    animation: fadeIn 0.5s ease-out;
}

.app-footer p { margin: 0.15rem 0; }

.app-footer .footer-brand {
    color: #334155;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
}

.app-footer .footer-links {
    margin-top: 0.5rem;
}

.app-footer .footer-links a {
    color: #059669;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s ease;
}

.app-footer .footer-links a:hover { color: #047857; }

/* ===== Divider ===== */
hr {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 1.5rem 0;
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ===== Mobile (<768px) ===== */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.25rem 0.75rem 1rem;
    }

    .header-icon { width: 44px; height: 44px; font-size: 1.3rem; border-radius: 11px; }
    .header-title { font-size: 1.4rem; }
    .header-subtitle { font-size: 0.85rem; }

    .step-num { width: 28px; height: 28px; font-size: 0.7rem; }
    .step-label { font-size: 0.68rem; }
    .step-line { width: 20px; }

    .stButton > button {
        width: 100%;
        padding: 0.75rem 1rem;
        font-size: 0.95rem;
    }

    .stCameraInput > div { width: 100% !important; }

    .badge { font-size: 0.7rem; padding: 0.2rem 0.6rem; }
    .price-big { font-size: 2rem; }
    .tip-card { font-size: 0.82rem; padding: 0.75rem 1rem; }
    .spec-box { font-size: 0.82rem; padding: 0.75rem 1rem; }
    .pay-card { padding: 1.25rem 1rem; }
}

/* ===== Tablet (768-1024px) ===== */
@media (min-width: 769px) and (max-width: 1024px) {
    .main .block-container { padding: 0.5rem 1.25rem 1.5rem; }
    .header-title { font-size: 1.8rem; }
    .step-label { font-size: 0.72rem; }
}

/* ===== Large screens ===== */
@media (min-width: 1025px) {
    .main .block-container { max-width: 1100px; }
}
</style>
"""


def inject_css():
    """Inject the responsive CSS into the Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_step_indicator(current_step):
    """Render a horizontal step progress indicator with connecting lines."""
    steps = [
        ("Country", "&#127760;"),
        ("Upload", "&#128247;"),
        ("Preview", "&#128065;"),
        ("Download", "&#11015;"),
    ]

    parts = ['<div class="step-bar">']
    for i, (label, icon) in enumerate(steps):
        if i > 0:
            if i < current_step:
                lc = "line-done"
            elif i == current_step:
                lc = "line-active"
            else:
                lc = "line-todo"
            parts.append(
                f'<div class="step-line-wrap"><div class="step-line {lc}"></div></div>'
            )

        if i < current_step:
            cls = "step-done"
            num = "&#10003;"
        elif i == current_step:
            cls = "step-active"
            num = str(i + 1)
        else:
            cls = "step-todo"
            num = str(i + 1)

        parts.append(
            f'<div class="step-group {cls}">'
            f'<div class="step-num">{num}</div>'
            f'<span class="step-label">{label}</span>'
            f"</div>"
        )

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
