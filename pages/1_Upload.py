
"""Private course library and PDF upload."""

import hashlib
import re

import streamlit as st

from core import (
    chunker,
    config,
    embeddings,
    pdf_parser,
    ui,
    vector_store,
)
from db import queries


st.set_page_config(
    page_title="Course Library · TutorLens",
    page_icon="📚",
    layout="wide",
)

ui.init()

student_id = ui.sidebar_student()


# ======================================
# PAGE HEADER
# ======================================

st.markdown(
    """
<div class="tl-hero">
<div class="tl-eyebrow">YOUR PERSONAL LEARNING MATERIALS</div>
<div class="tl-hero-title">Course <span class="tl-hero-accent">Library.</span></div>
<div class="tl-hero-description">Upload, organize and manage your course PDFs in your private learning workspace.</div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")


# ======================================
# PERSONAL LIBRARY STATISTICS
# ======================================

documents = queries.list_documents(student_id)

total_pages = sum(
    doc["n_pages"] for doc in documents
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "My documents",
        len(documents),
    )

with col2:
    st.metric(
        "Total pages",
        total_pages,
    )

with col3:
    st.metric(
        "Workspace",
        "Private",
    )


# ======================================
# PDF UPLOAD
# ======================================

st.markdown("## Upload course material")

st.caption(
    "Upload lecture notes, presentation slides "
    "or textbook chapters in PDF format."
)

uploaded = st.file_uploader(
    "Drag and drop your PDF here, or browse",
    type=["pdf"],
    key="private_pdf_upload",
)

if uploaded is not None:

    data = uploaded.getvalue()

    file_hash = hashlib.sha256(
        data
    ).hexdigest()

    existing = queries.get_document_by_hash(
        file_hash,
        student_id,
    )

    if existing:

        st.info(
            f"This PDF is already in your library: "
            f"{existing['title']}"
        )

        if st.button(
            "Open AI Tutor",
            type="primary",
        ):

            st.session_state["doc_id"] = (
                existing["id"]
            )

            st.switch_page(
                "pages/2_Learn.py"
            )

    elif st.button(
        "Process PDF",
        type="primary",
        use_container_width=True,
    ):

        try:

            with st.status(
                "Processing your course material...",
                expanded=True,
            ) as status:

                st.write("Reading the PDF...")

                parsed = pdf_parser.parse_pdf(data)

                st.info("Text-based extraction: image-only diagrams and screenshots are not interpreted.")
                chunks = chunker.build_chunks(parsed)

                if not chunks:

                    raise ValueError(
                        "No text could be extracted "
                        "from this PDF."
                    )

                st.write(
                    f"Found {parsed.n_pages} pages "
                    f"and {len(chunks)} text chunks."
                )

                st.write(
                    "Creating AI embeddings..."
                )

                bar = st.progress(0.0)

                vectors = embeddings.embed_texts(
                    [
                        c.for_embedding
                        for c in chunks
                    ],
                    progress=lambda done, total: (
                        bar.progress(done / total)
                    ),
                )

                title = re.sub(
                    r"\.pdf$",
                    "",
                    uploaded.name,
                    flags=re.IGNORECASE,
                )

                # Associate PDF with logged-in student
                doc_id = queries.add_document(
                    title,
                    uploaded.name,
                    file_hash,
                    parsed.n_pages,
                    student_id,
                )

                try:

                    vector_store.add_document_chunks(
                        doc_id,
                        chunks,
                        vectors,
                    )

                    (
                        config.PDF_DIR
                        / f"{doc_id}.pdf"
                    ).write_bytes(data)

                except Exception:

                    queries.delete_document(
                        doc_id,
                        student_id,
                    )

                    vector_store.delete_document(
                        doc_id
                    )

                    raise

                status.update(
                    label="Your PDF is ready!",
                    state="complete",
                )

            st.session_state["doc_id"] = doc_id

            st.session_state["upload_success"] = (
                "PDF successfully added to your library."
            )

            st.rerun()

        except Exception as error:

            st.error(
                f"Could not process this PDF: {error}"
            )


if st.session_state.get("upload_success"):

    st.success(
        st.session_state.pop("upload_success")
    )


# ======================================
# PRIVATE COURSE LIBRARY
# ======================================

st.divider()

st.markdown("## My course materials")

st.caption(
    "Only documents belonging to your "
    "student account are displayed here."
)

documents = queries.list_documents(student_id)

if not documents:

    st.info(
        "Your course library is empty. "
        "Upload your first PDF to start learning."
    )

else:

    for doc in documents:

        with st.container(border=True):

            left, right = st.columns([4, 2])

            with left:

                st.markdown(
                    f"### 📄 {doc['title']}"
                )

                st.caption(
                    f"{doc['n_pages']} pages "
                    "· Ready for learning"
                )

                st.caption(
                    "🔒 Private course material"
                )

            with right:

                if st.button(
                    "Start learning",
                    key=f"learn_{doc['id']}",
                    type="primary",
                    use_container_width=True,
                ):

                    st.session_state["doc_id"] = (
                        doc["id"]
                    )

                    st.switch_page(
                        "pages/2_Learn.py"
                    )

                if st.button(
                    "Take a quiz",
                    key=f"quiz_{doc['id']}",
                    use_container_width=True,
                ):

                    st.session_state["doc_id"] = (
                        doc["id"]
                    )

                    st.switch_page(
                        "pages/3_Quiz.py"
                    )

                confirm_delete = st.checkbox(
                    "Confirm deletion",
                    key=f"confirm_{doc['id']}",
                )

                if st.button(
                    "Delete PDF",
                    key=f"delete_{doc['id']}",
                    disabled=not confirm_delete,
                    use_container_width=True,
                ):

                    queries.delete_document(
                        doc["id"],
                        student_id,
                    )

                    vector_store.delete_document(
                        doc["id"]
                    )

                    (
                        config.PDF_DIR
                        / f"{doc['id']}.pdf"
                    ).unlink(missing_ok=True)

                    if (
                        st.session_state.get("doc_id")
                        == doc["id"]
                    ):

                        st.session_state.pop(
                            "doc_id",
                            None,
                        )

                    st.rerun()


# ======================================
# FOOTER
# ======================================

st.divider()

st.markdown(
    """
<div class="tl-footer">
<strong>TutorLens Course Library</strong><br>
Your materials. Your workspace. Your learning journey.
</div>
""",
    unsafe_allow_html=True,
)
