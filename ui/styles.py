"""Responsive CSS styles for the passport photo editor.

Clean, elegant design with smooth gradients, cards, and full
mobile/tablet/desktop responsiveness.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
/* ===== Hide Streamlit chrome ===== */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* ===== Global ===== */
.main .block-container {
    max-width: 1100px;
    padding: 0.5rem 1.5rem 2rem;
}

/* ===== App Header ===== */
.app-header {
    text-align: center;
    padding: 2rem 1rem 1rem;
}

.header-icon {
    font-size: 3rem;
    margin-bottom: 0.25rem;
}

.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.header-subtitle {
    color: #64748B;
    font-size: 1rem;
    max-width: 600px;
    margin: 0.75rem auto 1rem;
    line-height: 1.6;
}

.header-badges {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.badge {
    background: #F0F9FF;
    border: 1px solid #BAE6FD;
    color: #0369A1;
    border-radius: 2rem;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 600;
}

/* ===== Step Progress Bar ===== */
.step-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0;
    margin: 0.5rem auto 1.5rem;
    max-width: 650px;
}

.step-num {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
}

.step-label {
    font-size: 0.78rem;
    font-weight: 600;
    margin-left: 0.35rem;
    white-space: nowrap;
}

.step-group {
    display: flex;
    align-items: center;
}

.step-line {
    width: 40px;
    height: 2px;
    flex-shrink: 0;
}

.step-done .step-num {
    background: #10B981;
    color: white;
}
.step-done .step-label { color: #10B981; }
.step-done + .step-line-wrap .step-line { background: #10B981; }

.step-active .step-num {
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    color: white;
    box-shadow: 0 2px 8px rgba(37,99,235,0.35);
}
.step-active .step-label { color: #2563EB; }

.step-todo .step-num {
    background: #E2E8F0;
    color: #94A3B8;
}
.step-todo .step-label { color: #94A3B8; }

.step-line-wrap {
    display: flex;
    align-items: center;
}

.line-done { background: #10B981; }
.line-active { background: linear-gradient(90deg, #10B981, #2563EB); }
.line-todo { background: #E2E8F0; }

/* ===== Section Titles ===== */
.section-label {
    text-align: center;
    color: #94A3B8;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.25rem;
}

/* ===== Tip Card ===== */
.tip-card {
    background: linear-gradient(135deg, #FEF3C7, #FDE68A);
    border-left: 4px solid #F59E0B;
    border-radius: 0.5rem;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    line-height: 1.65;
    color: #92400E;
}

.tip-card b { color: #78350F; }

/* ===== Spec Box ===== */
.spec-box {
    background: linear-gradient(135deg, #F0F9FF, #E0F2FE);
    border: 1px solid #BAE6FD;
    border-radius: 0.5rem;
    padding: 1.15rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    line-height: 1.8;
}

.spec-box b { color: #0369A1; }

.spec-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0C4A6E;
    margin-bottom: 0.5rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #BAE6FD;
}

/* ===== Country Badge ===== */
.country-tag {
    display: inline-block;
    background: linear-gradient(135deg, #DBEAFE, #EDE9FE);
    border: 1px solid #C7D2FE;
    border-radius: 2rem;
    padding: 0.35rem 1rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: #4338CA;
    margin-bottom: 0.5rem;
}

/* ===== Photo Container ===== */
.photo-box {
    border: 2px solid #E2E8F0;
    border-radius: 0.75rem;
    padding: 0.5rem;
    background: #F8FAFC;
    text-align: center;
    transition: border-color 0.2s;
}

.photo-box:hover { border-color: #2563EB; }

.photo-box-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.4rem;
    margin-bottom: 0.2rem;
}

/* ===== Validation ===== */
.val-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
}

.val-pass { color: #10B981; font-weight: 500; padding: 0.2rem 0; font-size: 0.88rem; }
.val-fail { color: #EF4444; font-weight: 500; padding: 0.2rem 0; font-size: 0.88rem; }
.val-pass b, .val-fail b { font-weight: 700; }

/* ===== Payment Card ===== */
.pay-card {
    background: white;
    border: 2px solid #E2E8F0;
    border-radius: 0.75rem;
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    max-width: 420px;
    margin: 1rem auto;
}

.pay-card h3 { color: #1E293B; margin: 0 0 0.5rem; }

.price-big {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #2563EB, #7C3AED);
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
    line-height: 1.8;
}

/* ===== Download Section ===== */
.dl-section {
    background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
    border: 1px solid #86EFAC;
    border-radius: 0.75rem;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
}

.dl-section h3 { color: #166534; margin: 0 0 0.25rem; }
.dl-section p { color: #15803D; font-size: 0.9rem; }

/* ===== Email Card ===== */
.email-card {
    background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
    border: 1px solid #93C5FD;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
}

/* ===== Buttons ===== */
.stButton > button {
    border-radius: 0.5rem;
    font-weight: 600;
    padding: 0.6rem 2rem;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(37,99,235,0.25);
}

/* ===== Footer ===== */
.app-footer {
    text-align: center;
    padding: 1rem 0 0.5rem;
    color: #64748B;
    font-size: 0.82rem;
    line-height: 1.5;
}

.app-footer p { margin: 0.15rem 0; }

/* ===== Mobile (<768px) ===== */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.25rem 0.75rem 1rem;
    }

    .header-icon { font-size: 2rem; }
    .header-title { font-size: 1.4rem; }
    .header-subtitle { font-size: 0.85rem; }

    .step-num { width: 26px; height: 26px; font-size: 0.7rem; }
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
    steps = ["Country", "Upload", "Preview", "Download"]

    parts = ['<div class="step-bar">']
    for i, label in enumerate(steps):
        # Connector line before step (except first)
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

        # Step circle + label
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
