"""Generate quiz and exercise questions from the PDF text."""
from __future__ import annotations

import random

from core import config, llm_client, vector_store, teacher
from models.schemas import Question, QuestionSet

TYPE_DESCRIPTIONS = {
    "mcq": 'mcq (multiple choice with exactly 4 options)',
    "short": "short (a short written answer)",
    "exercise": "exercise (a small problem to solve)",
}


def select_chunks(chunks: list[dict], n_questions: int, rng: random.Random | None = None) -> list[dict]:
    """Pick a spread of chunks to base the questions on (pure function)."""
    rng = rng or random.Random()
    wanted = min(len(chunks), max(3, n_questions))
    picked: list[dict] = []
    total = 0
    for chunk in rng.sample(chunks, len(chunks)):
        if len(picked) >= wanted:
            break
        if total + len(chunk["text"]) > config.SECTION_CONTEXT_CHARS and picked:
            continue
        picked.append(chunk)
        total += len(chunk["text"])
    return sorted(picked, key=lambda c: c["chunk_index"])


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"[p.{c['page']} | {teacher.sanitize_personal_information(c['section'])}]\n{teacher.sanitize_personal_information(c['text'])}" for c in chunks)



def clean_questions(
    questions: list[Question], allowed_pages: set[int], allowed_types: set[str], n: int
) -> list[Question]:
    """Remove invalid questions and randomize MCQ answer options."""

    seen: set[str] = set()
    result: list[Question] = []

    for q in questions:
        key = q.question.strip().lower()

        if key in seen or q.type not in allowed_types:
            continue

        # Validate and shuffle MCQ options
        if q.type == "mcq":
            if len(q.options) != 4:
                continue

            if len({opt.strip().lower() for opt in q.options}) != 4:
                continue

            if q.answer not in q.options:
                continue

            random.shuffle(q.options)

        if q.source_page not in allowed_pages:
            continue

        seen.add(key)

        result.append(q)

    return result[:n]



def generate_quiz(
    doc_id: int,
    n: int = 5,
    difficulty: str = "mixed",
    types: list[str] | None = None,
    section: str | None = None,
) -> list[Question]:
    types = types or ["mcq", "short"]
    chunks = vector_store.get_section_chunks(doc_id, section) if section else vector_store.get_all_chunks(doc_id)
    if not chunks:
        raise RuntimeError("This PDF has no text to make questions from.")
    chosen = select_chunks(chunks, n)

    prompt = config.render_prompt(
        "question_gen",
        n=n,
        difficulty="a mix of easy, medium and hard" if difficulty == "mixed" else difficulty,
        types=", ".join(TYPE_DESCRIPTIONS[t] for t in types),
        context=build_context(chosen),
    )
    result = llm_client.chat_validated(
        [{"role": "user", "content": prompt}], QuestionSet, temperature=config.TEMP_JSON
    )
    questions = clean_questions(
        result.questions, {c["page"] for c in chosen}, set(types), n
    )
    if not questions:
        raise RuntimeError("The model did not produce usable questions. Please try again.")
    return questions