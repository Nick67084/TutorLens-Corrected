
"""TutorLens — AI-powered learning workspace."""

from pathlib import Path

import streamlit as st

from core import config, llm_client, ui
from db import queries


# ======================================
# PAGE CONFIGURATION
# ======================================

st.set_page_config(
    page_title="TutorLens | AI Learning Workspace",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.init()

# Require authentication before accessing the workspace
if not st.session_state.get("account"):
    ui.login_screen()
    st.stop()

student_id = ui.sidebar_student()


# ======================================
# SYSTEM STATUS
# ======================================

ok, message = llm_client.check_ollama()

documents = queries.list_documents(student_id)

with st.sidebar:
    st.divider()
    st.markdown("### AI system")

    if ok:
        st.success("AI engine connected")
    else:
        st.error("AI engine offline")

    st.caption(
        f"Model: {config.OLLAMA_MODEL or 'Not configured'}"
    )


# ======================================
# PAGE NAVIGATION
# ======================================

def open_page(page_name: str) -> None:
    """Find an existing Streamlit page by its filename."""

    pages_dir = Path(__file__).resolve().parent / "pages"

    matches = [
        page
        for page in pages_dir.glob("*.py")
        if page_name.lower() in page.stem.lower()
    ]

    if matches:
        page = sorted(matches)[0]
        st.switch_page(f"pages/{page.name}")
    else:
        st.warning(
            f"Please open the {page_name} page "
            "from the sidebar."
        )


# ======================================
# HERO SECTION
# ======================================

st.caption("WORKSPACE / HOME")


st.markdown(
    """
<div class="tl-hero">
<div class="tl-eyebrow">AI-POWERED PERSONALIZED EDUCATION</div>
<div class="tl-hero-title">
Learn smarter.<br>
<span class="tl-hero-accent">Study with TutorLens.</span>
</div>
<div class="tl-hero-description">
Transform your university course materials into an interactive
learning experience. Understand difficult concepts, generate
personalized quizzes, and track your academic progress with
your own AI tutor.
</div>
</div>
""",
    unsafe_allow_html=True,
)


action1, action2, empty = st.columns([1, 1, 2])

with action1:
    if st.button(
        "Start learning",
        type="primary",
        use_container_width=True,
        key="hero_learn",
    ):
        open_page("Learn")

with action2:
    if st.button(
        "Upload course PDF",
        use_container_width=True,
        key="hero_upload",
    ):
        open_page("Upload")


# ======================================
# WORKSPACE OVERVIEW
# ======================================

st.markdown("## Your workspace")

account = st.session_state["account"]

student_name = account["name"]

st.write(f"Welcome back, {student_name}!")

st.caption(
    f"Student ID: {account['login_id']} "
    "· Personal learning workspace"
)

quiz_history = queries.get_quiz_summary(student_id)

total_points = sum(
    quiz["points"]
    for quiz in quiz_history
)

total_max_points = sum(
    quiz["max_points"]
    for quiz in quiz_history
)

overall_score = (
    total_points / total_max_points * 100
    if total_max_points > 0
    else 0
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "My course materials",
        len(documents),
    )

with col2:

    st.metric(
        "Completed quizzes",
        len(quiz_history),
    )

with col3:

    st.metric(
        "Overall score",
        f"{overall_score:.1f}%"
        if total_max_points > 0
        else "—",
    )

with col4:

    st.metric(
        "AI tutor",
        "Online" if ok else "Offline",
    )


if not ok:
    st.warning(message)


# ======================================
# FEATURE CARDS
# ======================================

st.markdown("## Your learning toolkit")

st.caption(
    "Everything you need to understand, practice, "
    "and master your course materials."
)



def feature_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    """Render a feature card."""

    st.markdown(
        f"""
<div class="tl-feature-card">
<div class="tl-feature-icon">{icon}</div>
<div class="tl-feature-title">{title}</div>
<div class="tl-feature-description">{description}</div>
</div>
""",
        unsafe_allow_html=True,
    )


left, right = st.columns(2, gap="medium")

with left:

    feature_card(
        "📄",
        "Course Library",
        "Upload your lecture PDFs and organize "
        "your course materials in one place.",
    )

    if st.button(
        "Open course library",
        key="card_upload",
        use_container_width=True,
    ):
        open_page("Upload")

    st.write("")

    feature_card(
        "📝",
        "Smart Quiz",
        "Generate personalized assessments from "
        "your course materials and receive feedback.",
    )

    if st.button(
        "Take a quiz",
        key="card_quiz",
        use_container_width=True,
    ):
        open_page("Quiz")


with right:

    feature_card(
        "🎓",
        "AI Tutor",
        "Ask questions, explore difficult concepts, "
        "and learn through personalized explanations.",
    )

    if st.button(
        "Open AI tutor",
        key="card_learn",
        use_container_width=True,
    ):
        open_page("Learn")

    st.write("")

    feature_card(
        "📊",
        "My Performance",
        "Review your quiz results, track your marks, "
        "and identify areas for improvement.",
    )

    if st.button(
        "View my performance",
        key="card_marks",
        use_container_width=True,
    ):
        open_page("Marks")


# ======================================
# HOW IT WORKS
# ======================================

st.markdown("## How TutorLens works")

step1, step2, step3, step4 = st.columns(4)

with step1:
    st.markdown("### 01")
    st.markdown("**Upload**")
    st.caption("Add your course PDF.")

with step2:
    st.markdown("### 02")
    st.markdown("**Learn**")
    st.caption("Ask your AI tutor questions.")

with step3:
    st.markdown("### 03")
    st.markdown("**Practice**")
    st.caption("Test yourself with AI quizzes.")

with step4:
    st.markdown("### 04")
    st.markdown("**Improve**")
    st.caption("Review your results and feedback.")


# ======================================
# TECHNOLOGY INFORMATION
# ======================================


st.markdown(
    """
<div class="tl-tech-banner">
<div class="tl-feature-title">
Built for intelligent learning
</div>
<div class="tl-feature-description">
TutorLens uses Retrieval-Augmented Generation (RAG)
to connect a local language model with your uploaded
course materials, providing contextual explanations
and PDF source references.
</div>
</div>
""",
    unsafe_allow_html=True,
)


with st.expander("AI technology and system information"):

    st.markdown(
        """
        - **Architecture:** Retrieval-Augmented Generation
        - **AI inference:** Local Ollama language model
        - **Retrieval:** Semantic vector similarity search
        - **Learning:** Context-aware AI tutoring
        - **Assessment:** AI-generated quizzes and feedback
        - **Interface:** Streamlit
        """
    )

    st.write(
        "**Language model:**",
        config.OLLAMA_MODEL or "Not configured",
    )

    st.write(
        "**Embedding model:**",
        config.EMBEDDING_MODEL,
    )

    st.write(
        "**AI connection:**",
        "Connected" if ok else "Disconnected",
    )


# ======================================
# FOOTER
# ======================================

st.divider()


st.markdown(
    """
<div class="tl-footer">
<strong>TutorLens</strong><br>
AI Course Project · Personalized Learning with RAG
<br><br>
Learn. Practice. Improve.
</div>
""",
    unsafe_allow_html=True,
)
