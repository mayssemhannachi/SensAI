import streamlit as st


COLORS = {
    "background": "#F5F7FB",
    "surface": "#FFFFFF",
    "surface_soft": "#F1F5F9",

    "text": "#1B2A41",
    "muted": "#68778C",
    "border": "#E2E8F0",

    "primary": "#6075B8",
    "primary_dark": "#40558F",
    "lavender": "#B5C1E8",

    "pink": "#EAB5C2",
    "pink_dark": "#C77D91",

    "turquoise": "#7CC7BC",
    "turquoise_dark": "#438F86",

    "yellow": "#EACB79",
    "yellow_dark": "#B79543",

    "peach": "#F5C6A5",
    "mint": "#BCE7D8",

    "score": "#6075B8",
    "success": "#438F86",
    "progression": "#C77D91",

    "danger": "#C56A7D",
    "white": "#FFFFFF",
}


def get_colors():
    return COLORS


def render_html(markup, unsafe_allow_html=True):
    st.html(markup.strip())


def apply_theme():
    render_html(
        f"""
        <style>

        /* =====================================================
           GOOGLE FONTS
        ===================================================== */

        @import url(
            'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Nunito:wght@400;600;700;800;900&display=swap'
        );


        /* =====================================================
           GLOBAL
        ===================================================== */

        html, body, [class*="css"] {{
            font-family: 'DM Sans', sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(
                    circle at 5% 10%,
                    rgba(181,193,232,0.22),
                    transparent 27%
                ),
                radial-gradient(
                    circle at 95% 15%,
                    rgba(124,199,188,0.15),
                    transparent 24%
                ),
                {COLORS["background"]};
        }}

        .main {{
            padding-top: 1rem;
        }}

        h1, h2, h3 {{
            font-family: 'Nunito', sans-serif !important;
            color: {COLORS["text"]};
            font-weight: 900 !important;
        }}

        p, span, label, div {{
            font-family: 'DM Sans', sans-serif;
        }}


        /* =====================================================
           HIDE STREAMLIT DEFAULT ELEMENTS
        ===================================================== */

        #MainMenu {{
            visibility: hidden;
        }}

        footer {{
            visibility: hidden;
        }}

        header {{
            background: transparent !important;
        }}

        [data-testid="stSidebarNav"] {{
            display: none;
        }}

        button[data-testid="stBaseButton-headerNoPadding"] {{
            min-width: 2.5rem !important;
            min-height: 2.5rem !important;
            border: 1px solid {COLORS["primary"]} !important;
            border-radius: 0.75rem !important;
            background: {COLORS["surface"]} !important;
            color: {COLORS["primary_dark"]} !important;
            box-shadow: 0 2px 8px rgba(24, 32, 51, 0.12) !important;
            opacity: 1 !important;
            visibility: visible !important;
            z-index: 1001 !important;
        }}

        button[data-testid="stBaseButton-headerNoPadding"] svg {{
            color: {COLORS["primary_dark"]} !important;
            fill: {COLORS["primary_dark"]} !important;
        }}


        /* =====================================================
           SIDEBAR
        ===================================================== */

        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(
                    180deg,
                    #FFFDFB 0%,
                    #F3EEFF 55%,
                    #EFE9FF 100%
                );

            border-right: 1px solid {COLORS["border"]};
        }}

        section[data-testid="stSidebar"] > div {{
            padding: 1.2rem 1rem;
        }}

        .sidebar-brand {{
            position: relative;
            overflow: hidden;

            background:
                linear-gradient(
                    135deg,
                    #C9BBF3,
                    #EFC1D0
                );

            border-radius: 26px;
            padding: 22px 18px;
            margin-bottom: 25px;

            box-shadow:
                0 15px 35px rgba(120, 94, 170, 0.16);
        }}

        .sidebar-brand::after {{
            content: "";
            position: absolute;

            width: 90px;
            height: 90px;

            border-radius: 50%;

            background: rgba(255,255,255,0.30);

            right: -30px;
            top: -35px;
        }}

        .brand-logo {{
            font-size: 34px;
            margin-bottom: 5px;
        }}

        .brand-title {{
            font-family: 'Nunito', sans-serif;
            font-weight: 900;
            font-size: 22px;
            color: {COLORS["text"]};
        }}

        .brand-subtitle {{
            font-size: 12px;
            color: rgba(24,32,51,0.68);
        }}


        /* =====================================================
           NAVIGATION BUTTONS
        ===================================================== */

        section[data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            border: none;
            border-radius: 16px;

            padding: 13px 16px;

            background: transparent;
            color: {COLORS["text"]};

            text-align: left;

            font-family: 'Nunito', sans-serif;
            font-weight: 800;

            transition:
                transform 0.18s ease,
                background 0.18s ease,
                box-shadow 0.18s ease;
        }}

        section[data-testid="stSidebar"] .stButton > button:hover {{
            transform: translateX(5px);

            background: rgba(155,134,215,0.14);

            box-shadow:
                0 7px 20px rgba(120,94,170,0.08);
        }}

        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background:
                linear-gradient(
                    135deg,
                    {COLORS["primary"]},
                    #B49FE8
                );

            color: white;

            box-shadow:
                0 10px 25px rgba(155,134,215,0.28);
        }}


        /* =====================================================
           PAGE HEADER
        ===================================================== */

        .page-header {{
            position: relative;
            overflow: hidden;

            padding: 26px 30px;

            margin-bottom: 24px;

            border-radius: 24px;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.98),
                    rgba(241,245,249,0.94)
                );

            border: 1px solid rgba(232,226,242,0.9);

            box-shadow:
                0 15px 45px rgba(91,74,130,0.07);
        }}

        .page-header::before {{
            content: "";

            position: absolute;

            width: 180px;
            height: 180px;

            border-radius: 50%;

            background: rgba(199,185,241,0.28);

            right: -60px;
            top: -90px;
        }}

        .page-header::after {{
            content: "";

            position: absolute;

            width: 110px;
            height: 110px;

            border-radius: 45% 55% 60% 40%;

            background: rgba(124,199,188,0.15);

            right: 100px;
            bottom: -60px;

            transform: rotate(20deg);
        }}

        .page-kicker {{
            color: {COLORS["primary_dark"]};
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }}

        .page-title {{
            font-family: 'Nunito', sans-serif;

            font-size: 34px;
            font-weight: 900;

            color: {COLORS["text"]};

            margin: 4px 0;
        }}

        .page-description {{
            color: {COLORS["muted"]};
            font-size: 14px;
        }}

        .page-meta {{
            color: {COLORS["primary_dark"]};
            font-size: 12px;
            font-weight: 700;
            margin-top: 12px;
        }}


        /* =====================================================
           KPI CARDS
        ===================================================== */

        .kpi-card {{
            position: relative;
            overflow: hidden;

            min-height: 142px;

            padding: 19px 21px;

            border-radius: 19px;

            border: 1px solid {COLORS["border"]};

            box-shadow:
                0 8px 24px rgba(27,42,65,0.055);

            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease;
        }}

        .kpi-card:hover {{
            transform: translateY(-6px);

            box-shadow:
                0 14px 32px rgba(27,42,65,0.10);
        }}

        .kpi-card::after {{
            content: "";

            position: absolute;

            width: 90px;
            height: 90px;

            border-radius: 50%;

            background: rgba(255,255,255,0.25);

            right: -25px;
            top: -25px;
        }}

        .kpi-lavender {{
            background: linear-gradient(
                135deg,
                #F0F3FC,
                #E4EAF8
            );
        }}

        .kpi-pink {{
            background: linear-gradient(
                135deg,
                #FBF1F3,
                #F5E2E7
            );
        }}

        .kpi-turquoise {{
            background: linear-gradient(
                135deg,
                #EDF8F6,
                #D9EEEA
            );
        }}

        .kpi-yellow {{
            background: linear-gradient(
                135deg,
                #FBF7EA,
                #F2EACD
            );
        }}

        .kpi-icon {{
            font-size: 24px;
            margin-bottom: 12px;
        }}

        .kpi-label {{
            color: {COLORS["muted"]};
            font-size: 13px;
            font-weight: 700;
        }}

        .kpi-value {{
            font-family: 'Nunito', sans-serif;

            font-size: 29px;
            font-weight: 900;

            color: {COLORS["text"]};

            margin-top: 3px;
        }}

        .kpi-description {{
            color: {COLORS["muted"]};
            font-size: 11px;
            margin-top: 4px;
        }}


        /* =====================================================
           SECTION
        ===================================================== */

        .section-title {{
            font-family: 'Nunito', sans-serif;

            font-size: 20px;
            font-weight: 900;

            color: {COLORS["text"]};

            margin-top: 20px;
            margin-bottom: 5px;
        }}

        .section-subtitle {{
            color: {COLORS["muted"]};
            font-size: 13px;
            margin-bottom: 15px;
        }}


        /* =====================================================
           CONTENT CARDS
        ===================================================== */

        .soft-card {{
            background: {COLORS["surface"]};

            border: 1px solid {COLORS["border"]};

            border-radius: 18px;

            padding: 20px;

            box-shadow:
                0 8px 24px rgba(27,42,65,0.05);
        }}


        /* =====================================================
           PATIENT CARD
        ===================================================== */

        .patient-card {{
            background: rgba(255,255,255,0.85);

            border: 1px solid {COLORS["border"]};

            border-radius: 24px;

            padding: 20px;

            margin-bottom: 14px;

            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease,
                border-color 0.2s ease;
        }}

        .patient-card:hover {{
            transform: translateY(-5px);

            border-color: {COLORS["lavender"]};

            box-shadow:
                0 16px 35px rgba(91,74,130,0.10);
        }}

        .patient-avatar {{
            width: 48px;
            height: 48px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 16px;

            background:
                linear-gradient(
                    135deg,
                    #CFC2F2,
                    #F2B9CA
                );

            font-family: 'Nunito', sans-serif;
            font-weight: 900;

            color: {COLORS["text"]};
        }}


        /* =====================================================
           BADGES
        ===================================================== */

        .badge {{
            display: inline-block;

            padding: 6px 11px;

            border-radius: 999px;

            font-size: 11px;
            font-weight: 800;
        }}

        .badge-positive {{
            background: #DDF3EC;
            color: #347F72;
        }}

        .badge-negative {{
            background: #FBE1E7;
            color: #A44B61;
        }}

        .badge-neutral {{
            background: #EEE9FA;
            color: #675A92;
        }}


        /* =====================================================
           TABLE
        ===================================================== */

        [data-testid="stDataFrame"] {{
            border-radius: 20px;
            overflow: hidden;
        }}


        /* =====================================================
           BUTTONS
        ===================================================== */

        .stButton > button {{
            border-radius: 15px;

            border: 1px solid {COLORS["border"]};

            font-family: 'Nunito', sans-serif;

            font-weight: 800;

            transition:
                transform 0.18s ease,
                box-shadow 0.18s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px);

            box-shadow:
                0 8px 20px rgba(91,74,130,0.10);
        }}


        /* =====================================================
           INPUTS
        ===================================================== */

        .stTextInput input,
        .stSelectbox div[data-baseweb="select"],
        .stDateInput input {{
            border-radius: 15px !important;
        }}


        /* =====================================================
           EXPANDER
        ===================================================== */

        [data-testid="stExpander"] {{
            border-radius: 20px;
            border: 1px solid {COLORS["border"]};
            background: rgba(255,255,255,0.7);
        }}


        /* =====================================================
           ANIMATIONS
        ===================================================== */

        @keyframes fadeUp {{
            from {{
                opacity: 0;
                transform: translateY(12px);
            }}

            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes float {{
            0%, 100% {{
                transform: translateY(0);
            }}

            50% {{
                transform: translateY(-6px);
            }}
        }}

        .animate {{
            animation: fadeUp 0.55s ease forwards;
        }}

        .floating {{
            animation: float 4s ease-in-out infinite;
        }}


        /* =====================================================
           MOBILE
        ===================================================== */

        @media (max-width: 900px) {{

            .page-title {{
                font-size: 27px;
            }}

            .page-header {{
                padding: 22px;
            }}

            .kpi-card {{
                margin-bottom: 12px;
            }}
        }}

        </style>
        """,
    )