"""
PRE-DELINQUENCY INTERVENTION PLATFORM (PROPER VERSION)
=======================================================

Operational workflow:
1. Dashboard shows ranked high-risk customers
2. Operator clicks customer
3. Sees risk breakdown + behavioral timeline
4. Tests scenarios (what if?)
5. Generates outreach
6. Logs action
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta

pio.templates.default = "plotly_dark"

# ============================================================================
# DESIGN TOKENS (DARK, ENTERPRISE, RISK-AWARE)
# ============================================================================

BG_APP = "#0B1220"             # Base background
BG_SURFACE = "#151A28"        # Primary surface (+~5% luminance)
BG_SURFACE_ALT = "#1C2233"    # Alternate surface
BG_CARD = "#111827"           # Card / panel

TEXT_PRIMARY = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"
TEXT_SUBTLE = "#6B7280"

BORDER_SUBTLE = "#23293A"
BORDER_STRONG = "#3B4257"

# Semantic risk colors (restrained, no neon)
RISK_LOW = "#22C55E"          # Muted green – calm
RISK_MEDIUM = "#EAB308"       # Subdued amber – caution
RISK_HIGH = "#EA580C"         # Deep orange – urgent
RISK_CRITICAL = "#DC2626"     # Restrained red – alarming

ACCENT_INFO = "#3B82F6"       # Neutral / informational
SPOTLIGHT_GLOW = "rgba(220, 38, 38, 0.12)"   # Subtle red halo for critical
SPOTLIGHT_HIGH = "rgba(234, 88, 12, 0.08)"   # Subtle orange for high

st.set_page_config(
    page_title="Pre-Delinquency Intervention Platform",
    page_icon="🏦",
    layout="wide"
)

# ============================================================================
# GLOBAL PAGE STYLING (CSS)
# ============================================================================

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

    /* Base: Dark, breathable */
    .stApp, html, body, [data-testid="stAppViewContainer"] {{
        background-color: {BG_APP};
        color: {TEXT_PRIMARY};
        font-family: "Montserrat", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}

    /* Section spacing – more breath between areas */
    [data-testid="stHorizontalBlock"] {{
        margin-bottom: 0.5rem;
    }}

    /* Sidebar – flat dark */
    [data-testid="stSidebar"] > div:first-child {{
        background-color: {BG_APP};
        border-right: 1px solid {BORDER_SUBTLE};
    }}

    [data-testid="stSidebar"] h1, h2, h3, p, label {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* Hero – compact, dark + hover */
    .app-hero {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        padding: 0.75rem 1rem;
        margin-bottom: 1.25rem;
        border-radius: 8px;
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_SUBTLE};
        color: {TEXT_PRIMARY};
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    .app-hero:hover {{
        border-color: {BORDER_STRONG};
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }}

    .app-hero-left {{ display: flex; align-items: center; gap: 0.75rem; }}

    .app-logo-mark {{
        width: 40px;
        height: 40px;
        border-radius: 8px;
        background-color: {BG_SURFACE_ALT};
        border: 1px solid {BORDER_SUBTLE};
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        color: {ACCENT_INFO};
        transition: background-color 0.2s ease, border-color 0.2s ease;
    }}

    .app-hero:hover .app-logo-mark {{
        background-color: rgba(59, 130, 246, 0.12);
        border-color: rgba(59, 130, 246, 0.35);
    }}

    .app-eyebrow {{
        font-size: 10px;
        letter-spacing: 0.12em;
        color: {TEXT_SUBTLE};
        margin-bottom: 0.1rem;
    }}

    .app-title {{
        font-size: 20px;
        font-weight: 600;
        margin: 0;
        color: {TEXT_PRIMARY};
    }}

    .app-subtitle {{
        font-size: 12px;
        color: {TEXT_MUTED};
        margin: 0.2rem 0 0;
    }}

    .app-hero-right {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.25rem;
        font-size: 11px;
        color: {TEXT_MUTED};
    }}

    .hero-pill {{
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        border: 1px solid {BORDER_SUBTLE};
        background-color: {BG_SURFACE_ALT};
        transition: background-color 0.2s ease, border-color 0.2s ease;
    }}

    .hero-pill:hover {{
        background-color: {BORDER_SUBTLE};
        border-color: {BORDER_STRONG};
    }}

    .hero-pill.secondary {{
        border-color: rgba(59, 130, 246, 0.4);
        background-color: rgba(59, 130, 246, 0.08);
        color: #93C5FD;
    }}

    .hero-pill.secondary:hover {{
        background-color: rgba(59, 130, 246, 0.15);
        border-color: rgba(59, 130, 246, 0.6);
    }}

    /* Tabs – hover polish */
    .stTabs [role="tablist"] {{
        gap: 0.25rem;
        border-bottom: 1px solid {BORDER_SUBTLE};
        padding-bottom: 0;
    }}

    .stTabs [role="tab"] {{
        font-size: 13px;
        font-weight: 500;
        padding: 0.5rem 0.75rem;
        color: {TEXT_MUTED};
        border-radius: 6px 6px 0 0;
        transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    }}

    .stTabs [role="tab"]:hover {{
        background-color: rgba(21, 26, 40, 0.6);
        color: {TEXT_PRIMARY};
    }}

    .stTabs [role="tab"][aria-selected="true"] {{
        color: {TEXT_PRIMARY};
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_SUBTLE};
        border-bottom-color: {BG_SURFACE};
    }}

    /* Buttons – hover polish */
    [data-testid="stButton"] > button {{
        background-color: {ACCENT_INFO} !important;
        color: {BG_APP} !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.9rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: background-color 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease !important;
    }}

    [data-testid="stButton"] > button:hover {{
        background-color: #60A5FA !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35) !important;
        transform: translateY(-1px);
    }}

    [data-testid="stButton"] > button:active {{
        transform: translateY(0);
    }}

    /* Download / secondary buttons */
    [data-testid="stDownloadButton"] > button {{
        border-radius: 6px !important;
        transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.15s ease !important;
    }}

    [data-testid="stDownloadButton"] > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }}

    /* Metrics – numbers dominate labels + hover */
    div[data-testid="stMetric"] {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }}

    div[data-testid="stMetric"]:hover {{
        border-color: {BORDER_STRONG};
        background-color: {BG_SURFACE_ALT};
    }}

    div[data-testid="stMetric"] > label {{
        color: {TEXT_SUBTLE};
        font-size: 11px;
        font-weight: 400;
    }}

    div[data-testid="stMetric"] > div:nth-child(2) {{
        color: {TEXT_PRIMARY};
        font-size: 18px;
        font-weight: 600;
    }}

    /* Risk badges – consistent, with hover */
    .risk-badge {{
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 5px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border: 1px solid;
        transition: opacity 0.2s ease, box-shadow 0.2s ease;
    }}

    .risk-badge:hover {{
        opacity: 0.9;
    }}

    .risk-badge-low {{
        background-color: rgba(34, 197, 94, 0.18);
        color: #86EFAC;
        border-color: rgba(34, 197, 94, 0.4);
    }}

    .risk-badge-medium {{
        background-color: rgba(234, 179, 8, 0.2);
        color: #FDE047;
        border-color: rgba(234, 179, 8, 0.45);
    }}

    .risk-badge-medium-high {{
        background-color: rgba(245, 158, 11, 0.22);
        color: #FCD34D;
        border-color: rgba(245, 158, 11, 0.5);
    }}

    .risk-badge-high {{
        background-color: rgba(234, 88, 12, 0.22);
        color: #FB923C;
        border-color: rgba(234, 88, 12, 0.45);
    }}

    .risk-badge-critical {{
        background-color: rgba(220, 38, 38, 0.28);
        color: #F87171;
        border-color: rgba(220, 38, 38, 0.55);
        box-shadow: 0 0 12px rgba(220, 38, 38, 0.15);
    }}

    .risk-badge-critical:hover {{
        box-shadow: 0 0 16px rgba(220, 38, 38, 0.25);
    }}

    /* Spotlight rows for high/critical in tables */
    .row-spotlight-critical {{
        background-color: {SPOTLIGHT_GLOW} !important;
        border-left: 3px solid {RISK_CRITICAL};
    }}

    .row-spotlight-high {{
        background-color: {SPOTLIGHT_HIGH} !important;
        border-left: 3px solid {RISK_HIGH};
    }}

    /* DataFrames – dark, subdued + row hover */
    [data-testid="stDataFrame"] table {{
        border-radius: 6px;
        border: 1px solid {BORDER_SUBTLE};
        background-color: {BG_SURFACE};
    }}

    [data-testid="stDataFrame"] thead tr th {{
        background-color: {BG_SURFACE_ALT};
        color: {TEXT_MUTED};
        font-size: 11px;
        font-weight: 500;
    }}

    [data-testid="stDataFrame"] tbody tr {{
        transition: background-color 0.15s ease;
        cursor: default;
    }}

    [data-testid="stDataFrame"] tbody tr:nth-child(even) {{
        background-color: rgba(23, 30, 45, 0.5);
    }}

    [data-testid="stDataFrame"] tbody tr:hover {{
        background-color: rgba(59, 130, 246, 0.08) !important;
    }}

    /* Selectbox, multiselect, text input – hover polish */
    [data-testid="stSelectbox"] > div, [data-testid="stMultiSelect"] > div {{
        transition: border-color 0.2s ease;
    }}

    [data-testid="stSelectbox"]:focus-within > div, [data-testid="stMultiSelect"]:focus-within > div {{
        border-color: {ACCENT_INFO} !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.3);
    }}

    [data-testid="stTextInput"] input {{
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    [data-testid="stTextInput"]:focus-within input {{
        border-color: {ACCENT_INFO} !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.25);
    }}

    /* Headings – hierarchy */
    h1, h2, h3, h4 {{
        color: {TEXT_PRIMARY};
        font-weight: 600;
    }}

    h2 {{ font-size: 18px; margin-top: 1.5rem; margin-bottom: 0.5rem; }}
    h3 {{ font-size: 15px; margin-top: 1rem; margin-bottom: 0.35rem; }}

    hr {{
        border: none;
        border-top: 1px solid {BORDER_SUBTLE};
        margin: 1.5rem 0;
    }}

    /* Expander / info boxes – muted + hover */
    [data-testid="stExpander"] {{
        border-radius: 6px;
        border: 1px solid {BORDER_SUBTLE};
        transition: border-color 0.2s ease;
    }}

    [data-testid="stExpander"]:hover {{
        border-color: {BORDER_STRONG};
    }}

    [data-testid="stAlert"], .stAlert {{
        border-radius: 6px;
        transition: box-shadow 0.2s ease;
    }}

    [data-testid="stAlert"]:hover, .stAlert:hover {{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }}

    /* Captions – supporting, faded */
    [data-testid="stCaptionContainer"] {{
        color: {TEXT_SUBTLE};
        font-size: 12px;
    }}

    .panel-metric {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
    }}

    .panel-metric:hover {{
        border-color: {BORDER_STRONG};
        background-color: {BG_SURFACE_ALT};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}

    .panel-metric-label {{
        color: {TEXT_SUBTLE};
        font-size: 11px;
        margin-bottom: 0.2rem;
    }}

    .panel-metric-value {{
        color: {TEXT_PRIMARY};
        font-size: 18px;
        font-weight: 600;
    }}

    /* Slider thumb – subtle polish */
    [data-testid="stSlider"] .stSlider > div > div {{
        transition: box-shadow 0.2s ease;
    }}

    [data-testid="stSlider"] .stSlider > div > div:hover {{
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# HELPERS: RISK BADGES & SPOTLIGHT
# ============================================================================

def risk_badge_html(level: str) -> str:
    """Return HTML for a risk badge with semantic color."""
    level_upper = (level or "LOW").upper()
    cls = "risk-badge-low"
    if level_upper == "CRITICAL":
        cls = "risk-badge-critical"
    elif level_upper == "HIGH":
        cls = "risk-badge-high"
    elif level_upper == "MEDIUM_HIGH":
        cls = "risk-badge-medium-high"
    elif level_upper == "MEDIUM":
        cls = "risk-badge-medium"
    return f'<span class="risk-badge {cls}">{level_upper.replace("_", " ")}</span>'


def metric_card_spotlight(label: str, value: str, is_critical: bool = False, is_high: bool = False) -> None:
    """Render a metric with optional spotlight for high/critical."""
    extra = ""
    if is_critical:
        extra = ' style="border-left: 3px solid ' + RISK_CRITICAL + '; background-color: ' + SPOTLIGHT_GLOW + ';"'
    elif is_high:
        extra = ' style="border-left: 3px solid ' + RISK_HIGH + '; background-color: ' + SPOTLIGHT_HIGH + ';"'
    st.markdown(
        f"""
        <div class="panel-metric"{extra}>
            <div class="panel-metric-label">{label}</div>
            <div class="panel-metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_data():
    df_decisions = pd.read_csv('unified_customer_decisions.csv')
    df_customers = pd.read_csv('customer_features_from_priority1.csv')

    # Align identifiers and bring over stress_score for dashboard displays
    df_decisions['customer_id'] = df_decisions['customer_id'].astype(str)
    df_customers['customer_id'] = df_customers['customer_id'].astype(str)
    df_decisions = df_decisions.merge(
        df_customers[['customer_id', 'stress_score']],
        on='customer_id',
        how='left'
    )

    # Ensure contact_method and urgency exist (fallbacks for new schema)
    if 'contact_method' not in df_decisions.columns:
        df_decisions['contact_method'] = df_decisions['risk_level'].map({
            'CRITICAL': 'CALL + APP PUSH',
            'HIGH': 'CALL',
            'MEDIUM_HIGH': 'APP PUSH',
            'MEDIUM': 'APP PUSH',
            'LOW': 'NO CONTACT'
        }).fillna('APP PUSH')
    if 'urgency' not in df_decisions.columns:
        df_decisions['urgency'] = df_decisions['risk_level'].map({
            'CRITICAL': 'HIGH',
            'HIGH': 'HIGH',
            'MEDIUM_HIGH': 'MEDIUM',
            'MEDIUM': 'MEDIUM',
            'LOW': 'LOW'
        }).fillna('MEDIUM')

    return df_decisions, df_customers

df_decisions, df_customers = load_data()

# ============================================================================
# HEADER
# ============================================================================

st.markdown(
    """
    <div class="app-hero">
        <div class="app-hero-left">
            <div class="app-logo-mark">PD</div>
            <div>
                <div class="app-eyebrow">Pre-delinquency intervention</div>
                <h1 class="app-title">Risk and intervention command center</h1>
                <p class="app-subtitle">Pre-emptive risk detection and intervention for priority customers.</p>
            </div>
        </div>
        <div class="app-hero-right">
            <div class="hero-pill">Priority 1 portfolio</div>
            <div class="hero-pill secondary">Early warning</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs(["Portfolio dashboard", "Customer analysis", "Batch actions"])

# ============================================================================
# TAB 1: DASHBOARD (RANKED LIST)
# ============================================================================

with tab1:
    st.subheader("Early risk overview")
    st.caption("Primary insight: focus on Critical and High first.")
    
    # Summary – Critical and High get spotlight
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical_count = (df_decisions['risk_level'] == 'CRITICAL').sum()
        metric_card_spotlight("Critical", f"{critical_count:,}", is_critical=True)
    
    with col2:
        high_count = (df_decisions['risk_level'] == 'HIGH').sum()
        metric_card_spotlight("High", f"{high_count:,}", is_high=True)
    
    with col3:
        med_count = (df_decisions['risk_level'] == 'MEDIUM').sum()
        st.metric("Medium", f"{med_count:,}")
    
    with col4:
        low_count = (df_decisions['risk_level'] == 'LOW').sum()
        st.metric("Low", f"{low_count:,}")
    
    st.markdown("")
    st.markdown("---")
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        risk_opts = ['CRITICAL', 'HIGH', 'MEDIUM_HIGH', 'MEDIUM', 'LOW']
        risk_filter = st.multiselect(
            "Filter by risk level",
            [r for r in risk_opts if r in df_decisions['risk_level'].values],
            default=['CRITICAL', 'HIGH']
        )
    
    with col2:
        search = st.text_input("Search Customer ID", placeholder="CUST_000001")
    
    # Build display
    df_display = df_decisions.copy()
    
    if risk_filter:
        df_display = df_display[df_display['risk_level'].isin(risk_filter)]
    
    if search:
        df_display = df_display[df_display['customer_id'].str.contains(search, case=False, na=False)]
    
    df_display = df_display.sort_values('default_probability', ascending=False)
    
    # Format display – risk level stays as text (visual distinction via column order)
    df_display['Risk level'] = df_display['risk_level']
    df_display['Risk %'] = (df_display['default_probability'] * 100).round(1).astype(str) + '%'
    df_display['Stress'] = df_display['stress_score'].round(1)
    # Derive a simple urgency tag from risk level if not present
    urgency_map = {
        'CRITICAL': 'High',
        'HIGH': 'High',
        'MEDIUM_HIGH': 'Medium',
        'MEDIUM': 'Medium',
        'LOW': 'Low'
    }
    df_display['urgency'] = df_display['risk_level'].map(urgency_map).fillna('Medium')
    
    st.dataframe(
        df_display[[
            'customer_id',
            'Risk level',
            'Risk %',
            'Stress',
            'recommended_action',
            'urgency'
        ]].rename(columns={
            'customer_id': 'Customer ID',
            'recommended_action': 'Recommended action',
            'urgency': 'Urgency'
        }).head(50),
        use_container_width=True,
        height=400
    )
    
    st.markdown("")
    st.markdown("---")
    
    # Charts – horizontal bars, dark theme, soft gridlines
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk distribution")
        st.caption("Share of portfolio by risk level. Higher bars = more exposure.")
        risk_counts = df_decisions['risk_level'].value_counts()
        order = ['CRITICAL', 'HIGH', 'MEDIUM_HIGH', 'MEDIUM', 'LOW']
        risk_counts = risk_counts.reindex([x for x in order if x in risk_counts.index]).fillna(0)
        def _risk_color(x):
            if x == 'CRITICAL': return RISK_CRITICAL
            if x == 'HIGH': return RISK_HIGH
            if x in ('MEDIUM_HIGH', 'MEDIUM'): return RISK_MEDIUM
            return RISK_LOW
        colors = [_risk_color(x) for x in risk_counts.index]
        fig_risk = go.Figure(data=[go.Bar(
            x=risk_counts.values,
            y=risk_counts.index,
            orientation='h',
            marker_color=colors,
        )])
        fig_risk.update_layout(
            margin=dict(l=60, r=20, t=20, b=40),
            paper_bgcolor=BG_SURFACE,
            plot_bgcolor=BG_SURFACE,
            xaxis=dict(gridcolor=BORDER_SUBTLE, zeroline=False),
            yaxis=dict(showgrid=False),
            font=dict(color=TEXT_MUTED, size=12),
            height=320,
            showlegend=False,
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        st.subheader("Action distribution")
        st.caption("Recommended actions. Prioritise top interventions.")
        action_counts = df_decisions['recommended_action'].value_counts()
        fig_action = go.Figure(data=[go.Bar(
            x=action_counts.index,
            y=action_counts.values,
            marker_color=ACCENT_INFO,
        )])
        fig_action.update_layout(
            margin=dict(l=40, r=20, t=20, b=80),
            paper_bgcolor=BG_SURFACE,
            plot_bgcolor=BG_SURFACE,
            xaxis=dict(showgrid=False, tickangle=-30),
            yaxis=dict(gridcolor=BORDER_SUBTLE),
            font=dict(color=TEXT_MUTED, size=12),
            height=320,
            showlegend=False,
        )
        st.plotly_chart(fig_action, use_container_width=True)

# ============================================================================
# TAB 2: CUSTOMER DETAIL ANALYSIS
# ============================================================================

with tab2:
    st.subheader("Customer risk analysis and scenario testing")
    
    # Customer selection
    selected_cust = st.selectbox(
        "Select Customer",
        df_customers['customer_id'].head(500),
        key="customer_select"
    )
    
    if selected_cust:
        cust_decision = df_decisions[df_decisions['customer_id'] == selected_cust].iloc[0]
        cust_data = df_customers[df_customers['customer_id'] == selected_cust].iloc[0]
        
        # ====== [1] RISK SUMMARY ======
        st.subheader("1. Risk summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**Risk level**")
            st.markdown(risk_badge_html(cust_decision['risk_level']), unsafe_allow_html=True)
        
        with col2:
            st.metric("Stress score", f"{cust_data['stress_score']:.0f}/100")
        
        with col3:
            st.metric("Default risk", f"{cust_decision['default_probability']:.0%}")
        
        with col4:
            st.metric("Trend", "Rising" if cust_data['stress_score'] > 60 else "Stable")
        
        # ====== [2] BEHAVIORAL SIGNALS ======
        st.subheader("2. Behavioural signals detected")
        
        def flag(v, bad): return "Elevated" if bad else "Normal"
        signals = pd.DataFrame({
            'Signal': [
                'Salary delays',
                'ATM withdrawals',
                'Failed debits',
                'Payment on-time ratio',
                'Discretionary spending',
                'Payday loans',
                'Savings depleted',
                'Utility late payments'
            ],
            'Value': [
                f"{max(0, cust_data['salary_delay_days']):.1f} days",
                f"{max(0, cust_data['atm_withdrawal_count']):.0f}/week",
                f"{max(0, cust_data['failed_debit_count']):.0f} failures",
                f"{cust_data['payment_ratio']:.0%}",
                f"₹{max(0, cust_data['discretionary_spending']):,.0f}",
                f"{max(0, cust_data['lending_app_transactions']):.0f} loans",
                f"{cust_data['savings_drawdown_ratio']:.0%}",
                f"{max(0, cust_data['utility_late_payment_count']):.0f} times"
            ],
            'Status': [
                flag(cust_data['salary_delay_days'], cust_data['salary_delay_days'] > 5),
                flag(cust_data['atm_withdrawal_count'], cust_data['atm_withdrawal_count'] > 6),
                flag(cust_data['failed_debit_count'], cust_data['failed_debit_count'] > 2),
                flag(cust_data['payment_ratio'], cust_data['payment_ratio'] < 0.80),
                flag(cust_data['discretionary_spending'], cust_data['discretionary_spending'] < 2000),
                flag(cust_data['lending_app_transactions'], cust_data['lending_app_transactions'] > 5),
                flag(cust_data['savings_drawdown_ratio'], cust_data['savings_drawdown_ratio'] > 0.40),
                flag(cust_data['utility_late_payment_count'], cust_data['utility_late_payment_count'] > 1),
            ]
        })
        
        st.dataframe(signals, use_container_width=True, hide_index=True)
        
        # ====== [3] PLAIN ENGLISH EXPLANATION ======
        st.subheader("3. Plain language explanation")
        
        if cust_decision['risk_level'] == 'CRITICAL':
            explanation = f"""
            **Critical risk – immediate action required**
            
            {selected_cust} is showing severe financial distress:
            - Salary delays: {cust_data['salary_delay_days']:.0f} days
            - ATM withdrawals: {cust_data['atm_withdrawal_count']:.0f}/week  
            - Payment failures: {cust_data['failed_debit_count']:.0f} recent failures
            - EMI payment rate: {cust_data['payment_ratio']:.0%} of obligations
            - Savings drawn: {cust_data['savings_drawdown_ratio']:.0%}
            - Short-term loans: {cust_data['lending_app_transactions']:.0f}
            
            **Risk assessment**: Default likely within 14–21 days without intervention.
            """
        
        elif cust_decision['risk_level'] == 'HIGH':
            explanation = f"""
            **High risk – urgent intervention recommended**
            
            {selected_cust} shows deteriorating financial health:
            - Salary delays averaging {cust_data['salary_delay_days']:.0f} days
            - Discretionary spending has reduced
            - {cust_data['failed_debit_count']:.0f} payment failures in past month
            - Increasing reliance on short-term credit
            
            **Risk assessment**: Default possible within 30–45 days if trend continues.
            """
        
        elif cust_decision['risk_level'] == 'MEDIUM':
            explanation = f"""
            **Medium risk – preventive outreach recommended**
            
            {selected_cust} shows early warning signs:
            - Minor delays in some payments ({cust_data['salary_delay_days']:.1f} days average)
            - Slightly elevated borrowing activity
            - Savings balance relatively stable ({cust_data['savings_drawdown_ratio']:.0%} drawn)
            
            **Risk assessment**: Early intervention can prevent escalation.
            """
        
        else:
            explanation = f"""
            **Low risk – routine monitoring**
            
            {selected_cust} shows healthy financial patterns:
            - Payments on time {cust_data['payment_ratio']:.0%} of the time
            - Stable savings balance
            - Minimal short-term borrowing
            
            **Risk assessment**: Continue routine monitoring. No immediate action needed.
            """
        
        st.info(explanation)
        
        # ====== [4] RECOMMENDED ACTION ======
        st.subheader("4. Recommended action")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            **Recommended action:** {cust_decision['recommended_action'].replace('_', ' ').title()}
            
            - **Duration:** 30–60 days  
            - **Contact method:** {cust_decision['contact_method']}  
            - **Urgency:** {cust_decision['urgency'].replace('_', ' ').title()}  
            - **Expected outcome:** Prevent default
            
            Financial stress detected. Proactive intervention can prevent default in the coming weeks.
            """)
        
        with col2:
            current_balance = max(0, cust_data['final_savings_balance'])
            monthly_salary = max(0, cust_data['monthly_salary'])
            
            st.metric("Current Savings", f"₹{current_balance:,.0f}")
            st.metric("Monthly Salary", f"₹{monthly_salary:,.0f}")
            st.metric("Balance (months)", f"{current_balance/max(monthly_salary, 1):.1f}")
        
        # ====== [5] SCENARIO TESTING ======
        st.subheader("5. Scenario testing – what if?")
        
        st.caption("Adjust income, EMI burden and expenses to see the impact on stress.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            salary_change = st.slider("Salary Change", -50, 50, 0, 5, key="salary") / 100
        
        with col2:
            emi_change = st.slider("EMI Burden Change", -50, 50, 0, 5, key="emi") / 100
        
        with col3:
            expense_change = st.slider("Expense Change", -50, 50, 0, 5, key="expense") / 100
        
        # Recalculate stress under scenario
        base_stress = cust_data['stress_score']
        
        # Stress increases with: expenses ↑, salary ↓, EMI ↑
        stress_multiplier = 1.0 + (expense_change * 0.4) - (salary_change * 0.6) + (emi_change * 0.5)
        new_stress = base_stress * stress_multiplier
        new_stress = max(0, min(100, new_stress))
        
        # Determine new risk level
        if new_stress > 85:
            scenario_risk = 'CRITICAL'
        elif new_stress > 65:
            scenario_risk = 'HIGH'
        elif new_stress > 35:
            scenario_risk = 'MEDIUM'
        else:
            scenario_risk = 'LOW'
        
        # Show impact
        if salary_change != 0 or emi_change != 0 or expense_change != 0:
            st.info(f"""
            **Scenario impact**
            
            Current state  
            - Stress score: {base_stress:.0f}/100  
            - Risk level: {cust_decision['risk_level']}  
            
            Under new scenario  
            - New stress score: {new_stress:.0f}/100 (change: {new_stress - base_stress:+.0f})  
            - New risk level: {scenario_risk}  
            - Recommended action: {cust_decision['recommended_action'].replace('_', ' ').title()}  
            """)
        
        # ====== [6] OUTREACH MESSAGE GENERATOR ======
        st.subheader("6. Outreach message template")
        
        if st.button("Generate personalised message", key="gen_msg"):
            
            action_details = {
                'PAYMENT_HOLIDAY': 'a temporary pause on your loan obligations',
                'LOAN_RESTRUCTURE': 'restructured payment terms',
                'PROACTIVE_OUTREACH': 'flexible repayment options',
                'STANDARD_MONITORING': 'continued standard service and support'
            }
            
            action_text = action_details.get(cust_decision['recommended_action'], 'support')
            
            message = f"""
Dear Valued Customer ({selected_cust}),

We value your relationship with us and want to ensure your financial wellbeing.

We've noticed some recent changes in your account activity that suggest you might be 
experiencing financial challenges. This is completely normal, and we're here to help.

**Offer:** We would like to offer you {action_text}. This can help you:
- Reduce immediate financial pressure
- Maintain your credit standing
- Preserve your account health

**Next steps:** Please contact us to discuss:
- Call: 1-800-BANK (1-800-2265)
- Email: support@bank.com

We're committed to working with you during this time. Our team will be happy to explain 
all available options and find the solution that works best for your situation.

Warm regards,
Your Bank Support Team

---
Reference: {selected_cust} | Risk Level: {cust_decision['risk_level']} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
            
            st.text_area("Generated message (edit before sending):", value=message, height=280)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Send email", key="email_btn"):
                    st.success(f"Email queued for {selected_cust}")
            
            with col2:
                if st.button("Send SMS", key="sms_btn"):
                    st.success(f"SMS queued for {selected_cust}")
            
            with col3:
                if st.button("Schedule call", key="call_btn"):
                    st.success(f"Call scheduled for {selected_cust}")
        
        # ====== [7] ACTION LOG ======
        st.subheader("7. Action log and audit trail")
        
        action_log = pd.DataFrame({
            'Date': ['Today ' + datetime.now().strftime("%H:%M %Z"), 'Yesterday 02:15 PM'],
            'Action': ['Risk Assessment Generated', 'Risk Flag Triggered'],
            'Status': ['Pending Intervention', 'Logged'],
            'Notes': [
                f'Stress score: {cust_data["stress_score"]:.0f}/100 - Recommended action: {cust_decision["recommended_action"]}',
                'Automated trigger by pre-delinquency detection system'
            ]
        })
        
        st.dataframe(action_log, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 3: BATCH ACTIONS
# ============================================================================

with tab3:
    st.subheader("Batch action management")
    st.caption("Top priority: Critical and high-risk customers needing intervention.")
    
    # Show all HIGH + CRITICAL – spotlight on Critical and High
    batch_df = df_decisions[df_decisions['risk_level'].isin(['CRITICAL', 'HIGH'])].sort_values('default_probability', ascending=False)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        metric_card_spotlight("Customers requiring action", f"{len(batch_df):,}")
    
    with col2:
        metric_card_spotlight("Critical priority", f"{len(batch_df[batch_df['risk_level'] == 'CRITICAL']):,}", is_critical=True)
    
    with col3:
        metric_card_spotlight("High priority", f"{len(batch_df[batch_df['risk_level'] == 'HIGH']):,}", is_high=True)
    
    st.markdown("")
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Download action list (CSV)"):
            csv = batch_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"intervention_list_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_csv"
            )
    
    with col2:
        if st.button("Send bulk messages"):
            st.success(f"{len(batch_df)} bulk messages queued")
    
    with col3:
        if st.button("Generate report"):
            st.success("Report generated and queued")
    
    st.markdown("")
    st.markdown("---")
    
    st.subheader("Top 50 customers requiring immediate action")
    st.caption("Focus on Critical first. Each row shows recommended action and contact method.")
    
    display_batch = batch_df.head(50).copy()
    
    display_batch['Risk level'] = display_batch['risk_level']
    display_batch['Risk %'] = (display_batch['default_probability'] * 100).round(1).astype(str) + '%'
    display_batch['Stress'] = display_batch['stress_score'].round(1)
    
    display_batch['Risk %'] = (display_batch['default_probability'] * 100).round(1).astype(str) + '%'
    display_batch['Stress'] = display_batch['stress_score'].round(1)
    
    st.dataframe(
        display_batch[[
            'customer_id',
            'Risk level',
            'Risk %',
            'Stress',
            'recommended_action',
            'contact_method'
        ]].rename(columns={
            'customer_id': 'Customer ID',
            'recommended_action': 'Action',
            'contact_method': 'Contact'
        }),
        use_container_width=True,
        height=400
    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Pre-Delinquency Intervention Platform | Barclays | February 2026")
