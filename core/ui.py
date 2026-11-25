
"""Shared UI components and styling for TutorLens."""

from __future__ import annotations

import streamlit as st

from db import database, queries


def apply_theme() -> None:
    """Apply the TutorLens visual identity."""

    st.markdown(
        """
        <style>

        /* ==============================
           GLOBAL COLORS
        ============================== */

        :root {
            --tl-primary: #10746D;
            --tl-dark: #0B3939;
            --tl-sidebar: #114949;
            --tl-white: #FFFFFF;
            --tl-background: #F1F8F6;
            --tl-mint: #E2F2EE;
            --tl-border: #B9DFD9;
            --tl-muted: #52716C;
            --tl-gold: #FFAD32;
        }

        .stApp {
            background-color: var(--tl-background);
        }

        .block-container {
            max-width: 1400px;
            padding-top: 5rem;
            padding-bottom: 3rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }

        h1, h2, h3 {
            color: var(--tl-dark);
            letter-spacing: -0.5px;
        }

        /* ==============================
           SIDEBAR
        ============================== */

        [data-testid="stSidebar"] {
            background: var(--tl-dark);
            border-right: 1px solid #285A56;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] a,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #FFFFFF;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 8px;
            margin: 3px 8px;
            transition: background 0.2s ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: #1C5551;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: var(--tl-primary);
        }

        [data-testid="stSidebar"] input {
            color: var(--tl-dark);
            background: #FFFFFF;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] {
            color: var(--tl-dark);
        }

        [data-testid="stSidebar"] [data-baseweb="select"] span {
            color: var(--tl-dark);
        }

        [data-testid="stSidebar"] .stButton > button {
    background-color: #10746D !important;
    border: 1px solid #B9DFD9 !important;
    color: #FFFFFF !important;
    border-radius: 9px;
}

[data-testid="stSidebar"] .stButton > button * {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #195653 !important;
    border-color: #FFFFFF !important;
}

        /* Sidebar download buttons share the same accessible teal theme. */
        [data-testid="stSidebar"] .stDownloadButton button,
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
            background-color: #10746D !important;
            border: 1px solid #B9DFD9 !important;
            color: #FFFFFF !important;
            border-radius: 9px;
        }
        [data-testid="stSidebar"] .stDownloadButton button *,
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] button * {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .stDownloadButton button:hover:not(:disabled),
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover:not(:disabled) {
            background-color: #195653 !important;
            border-color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .stDownloadButton button:disabled,
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        .tl-brand {
            padding: 12px 0 18px 0;
            border-bottom: 1px solid #40706C;
            margin-bottom: 18px;
        }

        .tl-brand-name {
            font-size: 29px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -1px;
        }

        .tl-brand-caption {
            color: #B9DFD9;
            font-size: 12px;
            letter-spacing: 1px;
            margin-top: 5px;
        }

        /* ==============================
           BUTTONS
        ============================== */

        .stButton > button,
        .stDownloadButton > button,
        .stPageLink a {
            border-radius: 9px;
            font-weight: 600;
            min-height: 44px;
            transition: all 0.2s ease;
        }

        .stButton > button[kind="primary"] {
            background: var(--tl-primary);
            border-color: var(--tl-primary);
            color: #FFFFFF;
        }

        .stButton > button[kind="primary"]:hover {
            background: var(--tl-dark);
            border-color: var(--tl-dark);
        }

        .stButton > button[kind="secondary"] {
            background: #FFFFFF;
            border: 1px solid var(--tl-border);
            color: var(--tl-dark);
        }

        .stButton > button[kind="secondary"]:hover {
            border-color: var(--tl-primary);
            background: var(--tl-mint);
        }

        /* ==============================
           METRIC CARDS
        ============================== */

        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--tl-border);
            border-radius: 12px;
            padding: 18px 20px;
        }

        [data-testid="stMetricValue"] {
            color: var(--tl-primary);
            font-weight: 700;
        }

        /* ==============================
           CHAT INTERFACE
        ============================== */

        [data-testid="stChatMessage"] {
            background: #FFFFFF;
            border: 1px solid #DCEBE7;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }

        [data-testid="stChatInput"] {
            border-radius: 12px;
        }

        /* ==============================
           DOCUMENTS AND TABLES
        ============================== */

        [data-testid="stFileUploaderDropzone"] {
            background: #FFFFFF;
            border: 2px dashed var(--tl-border);
            border-radius: 12px;
            padding: 20px;
        }

        [data-testid="stDataFrame"] {
            border-radius: 10px;
            overflow: hidden;
        }

        [data-testid="stExpander"] {
            background: #FFFFFF;
            border-radius: 10px;
        }

        /* ==============================
           HOME PAGE
        ============================== */

        .tl-hero {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(
                    circle at 90% 15%,
                    #195653 0%,
                    transparent 45%
                ),
                linear-gradient(
                    125deg,
                    #0B3939,
                    #114949
                );
            border-radius: 20px;
            padding: 48px 42px;
            margin-bottom: 24px;
            color: #FFFFFF;
        }

        .tl-eyebrow {
            color: #FFAD32;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 3px;
            margin-bottom: 18px;
        }

        .tl-hero-title {
            font-family: Georgia, serif;
            font-size: clamp(34px, 4vw, 54px);
            line-height: 1.15;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 20px;
        }

        .tl-hero-accent {
            color: #B9DFD9;
        }

        .tl-hero-description {
            color: #D8EDE9;
            font-size: 16px;
            line-height: 1.7;
            max-width: 680px;
        }

        .tl-feature-card {
            background: #FFFFFF;
            border: 1px solid var(--tl-border);
            border-radius: 14px;
            padding: 24px;
            min-height: 180px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
        }

        .tl-feature-card:hover {
            border-color: var(--tl-primary);
            box-shadow: 0 5px 20px rgba(11,57,57,0.07);
        }

        .tl-feature-icon {
            background: var(--tl-mint);
            color: var(--tl-primary);
            display: inline-block;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 23px;
            margin-bottom: 12px;
        }

        .tl-feature-title {
            color: var(--tl-dark);
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .tl-feature-description {
            color: var(--tl-muted);
            font-size: 14px;
            line-height: 1.6;
        }

        .tl-tech-banner {
            background: var(--tl-mint);
            border: 1px solid var(--tl-border);
            border-radius: 12px;
            padding: 22px;
            margin-top: 20px;
        }

        .tl-footer {
            color: var(--tl-muted);
            text-align: center;
            font-size: 12px;
            padding: 25px 0 10px 0;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .tl-hero {
                padding: 28px 22px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )



def init() -> None:
    """Initialize the database and shared theme."""
    database.init_db()
    apply_theme()


# ======================================
# LOGIN AND REGISTRATION
# ======================================

def login_screen():

    from core import auth

    st.markdown(
        """
<div class="tl-hero">
<div class="tl-eyebrow">YOUR PERSONAL AI LEARNING WORKSPACE</div>
<div class="tl-hero-title">
Welcome to <span class="tl-hero-accent">TutorLens.</span>
</div>
<div class="tl-hero-description">
Sign in to access your private course materials,
AI conversations, quizzes and academic performance.
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.write("")

    left, right = st.columns([1, 1], gap="large")

    with left:

        st.markdown("## Your learning journey")

        st.markdown(
            """
            TutorLens provides a personalized learning
            experience powered by artificial intelligence.

            **Your personal workspace includes:**

            - Private course PDF library
            - Personalized AI tutoring
            - Saved conversation history
            - AI-generated quizzes
            - Individual marks and feedback
            """
        )

        st.info(
            "Your learning records are linked "
            "to your individual student account."
        )

    with right:

        login, signup = st.tabs(
            ["Sign in", "Create account"]
        )

        # ======================================
        # SIGN IN
        # ======================================

        with login:

            st.markdown("### Welcome back")

            st.caption(
                "Sign in to your personal workspace."
            )

            with st.form(
                "login",
                clear_on_submit=True,
            ):

                login_id = st.text_input(
                    "Student ID",
                    placeholder="Enter your student ID",
                    key="login_id",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password",
                )

                submitted = st.form_submit_button(
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:

                    account = auth.authenticate(
                        login_id,
                        password,
                    )

                    if account:

                        st.session_state.clear()

                        st.session_state["account"] = (
                            account
                        )

                        st.session_state["student_name"] = (
                            account["name"]
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Invalid student ID or password."
                        )

        # ======================================
        # CREATE ACCOUNT
        # ======================================

        with signup:

            st.markdown("### Create your account")

            st.caption(
                "Start your personalized learning journey."
            )

            with st.form(
                "register",
                clear_on_submit=True,
            ):

                name = st.text_input(
                    "Full name",
                    placeholder="Enter your full name",
                    key="register_name",
                )

                login_id = st.text_input(
                    "Student ID",
                    placeholder="Enter your student ID",
                    key="register_id",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                    key="register_password",
                )

                confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="register_confirm",
                )

                submitted = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:

                    try:

                        if password != confirm:
                            raise ValueError(
                                "Passwords do not match."
                            )

                        auth.register(
                            name,
                            login_id,
                            password,
                        )

                        st.success(
                            "Account created successfully! "
                            "Please switch to Sign in."
                        )

                    except ValueError as error:

                        st.error(str(error))

    st.divider()

    st.markdown(
        """
<div class="tl-footer">
<strong>TutorLens</strong><br>
Private and Personalized AI Learning Workspace
<br><br>
Learn. Practice. Improve.
</div>
""",
        unsafe_allow_html=True,
    )


# ======================================
# AUTHENTICATED STUDENT PROFILE
# ======================================

def sidebar_student() -> int:

    account = st.session_state.get("account")

    if not account:

        st.switch_page("main.py")
        st.stop()

    st.sidebar.title("TutorLens")

    st.sidebar.markdown("### Student profile")

    st.sidebar.write(account["name"])

    st.sidebar.caption(
        "Student ID: " + account["login_id"]
    )

    st.sidebar.markdown(
        '<div style="background:#114949;border:1px solid #10746D;'
        'border-radius:10px;padding:12px 16px;color:#FFFFFF;">'
        '<span style="color:#86EFAC;">●</span> &nbsp; Signed in</div>',
        unsafe_allow_html=True,
    )

    if st.sidebar.button(
        "Log out",
        use_container_width=True,
    ):

        st.session_state.clear()

        st.switch_page("main.py")

    return account["id"]


# ======================================
# PRIVATE COURSE MATERIAL SELECTOR
# ======================================

def sidebar_document() -> dict | None:

    account = st.session_state.get("account")

    if not account:

        st.switch_page("main.py")
        st.stop()

    documents = queries.list_documents(
        account["id"]
    )

    if not documents:

        st.sidebar.info(
            "No course materials uploaded yet."
        )

        return None

    ids = [d["id"] for d in documents]

    by_id = {
        d["id"]: d
        for d in documents
    }

    saved = st.session_state.get("doc_id")

    index = ids.index(saved) if saved in ids else 0

    st.sidebar.markdown("### Course material")

    chosen = st.sidebar.selectbox(
        "Course PDF",
        ids,
        index=index,
        format_func=lambda doc_id: (
            f"{by_id[doc_id]['title']} "
            f"({by_id[doc_id]['n_pages']} pages)"
        ),
    )

    st.session_state["doc_id"] = chosen

    return by_id[chosen]


# ======================================
# PDF SOURCE REFERENCES
# ======================================

def format_sources(sources) -> str:

    seen: dict[int, str] = {}

    for source in sources:

        seen.setdefault(
            source.page,
            source.section,
        )

    parts = [
        f"p.{page} ({section[:40]})"
        for page, section in sorted(seen.items())
    ]

    return "Sources: " + " · ".join(parts)
