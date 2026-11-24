"""All database reads and writes used by the app. Every function returns plain
Python values (ints, dicts, lists) so the pages never touch SQLAlchemy objects."""
from sqlalchemy import delete, func, select

from db.database import get_session
from db.tables import Attempt, Document, QuestionRow, Student, Conversation, Account
from models.schemas import GradeResult, Question


# ---- students ------------------------------------------------------------
def get_or_create_student(name: str) -> int:
    with get_session() as session:
        student = session.scalar(select(Student).where(Student.name == name))
        if student is None:
            student = Student(name=name)
            session.add(student)
            session.flush()
        return student.id


# ---- documents -----------------------------------------------------------
def _document_dict(doc: Document) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "filename": doc.filename,
        "file_hash": doc.file_hash,
        "n_pages": doc.n_pages,
        "uploaded_at": doc.uploaded_at,
    }


def add_document(title: str, filename: str, file_hash: str, n_pages: int, owner_id: int | None = None) -> int:
    with get_session() as session:
        doc = Document(owner_id=owner_id, title=title, filename=filename, file_hash=file_hash, n_pages=n_pages)
        session.add(doc)
        session.flush()
        return doc.id


def get_document_by_hash(file_hash: str, owner_id: int | None = None) -> dict | None:
    with get_session() as session:
        doc = session.scalar(select(Document).where(Document.file_hash == file_hash, Document.owner_id == owner_id))
        return _document_dict(doc) if doc else None


def list_documents(owner_id: int | None = None) -> list[dict]:
    with get_session() as session:
        docs = session.scalars(select(Document).where(Document.owner_id == owner_id).order_by(Document.id)).all()
        return [_document_dict(d) for d in docs]


def delete_document(doc_id: int, owner_id: int | None = None) -> None:
    """Delete a document together with its questions and attempts."""
    with get_session() as session:
        require_document(session, doc_id, owner_id)
        session.execute(delete(Conversation).where(Conversation.document_id == doc_id))
        question_ids = select(QuestionRow.id).where(QuestionRow.document_id == doc_id)
        session.execute(delete(Attempt).where(Attempt.question_id.in_(question_ids)))
        session.execute(delete(QuestionRow).where(QuestionRow.document_id == doc_id))
        session.execute(delete(Document).where(Document.id == doc_id))


# ---- questions -----------------------------------------------------------
def next_quiz_no(doc_id: int, owner_id: int | None = None) -> int:
    with get_session() as session:
        require_document(session, doc_id, owner_id)
        current = session.scalar(
            select(func.max(QuestionRow.quiz_no)).where(QuestionRow.document_id == doc_id)
        )
        return (current or 0) + 1


def save_questions(doc_id: int, quiz_no: int, questions: list[Question], owner_id: int | None = None) -> list[int]:
    with get_session() as session:
        require_document(session, doc_id, owner_id)
        rows = [
            QuestionRow(
                document_id=doc_id,
                quiz_no=quiz_no,
                topic=q.topic,
                difficulty=q.difficulty,
                type=q.type,
                question=q.question,
                options=q.options,
                answer=q.answer,
                rubric=q.rubric,
                source_page=q.source_page,
            )
            for q in questions
        ]
        session.add_all(rows)
        session.flush()
        return [row.id for row in rows]


# ---- attempts and marks --------------------------------------------------
def save_attempt(student_id: int, question_id: int, answer_text: str | None, grade: GradeResult) -> None:
    save_quiz_attempts(student_id, [(question_id, answer_text, grade)])


def save_quiz_attempts(student_id: int, attempts: list[tuple[int, str | None, GradeResult]]) -> None:
    """Save all graded answers in one transaction."""
    with get_session() as session:
        for question_id, answer_text, grade in attempts:
            question = session.get(QuestionRow, question_id)
            if question is None:
                raise PermissionError("Question unavailable")
            require_document(session, question.document_id, student_id)
            existing = session.scalar(select(Attempt.id).where(
                Attempt.student_id == student_id, Attempt.question_id == question_id
            ).limit(1))
            if existing is not None:
                raise ValueError("This question has already been submitted.")
            session.add(Attempt(
                student_id=student_id, question_id=question_id,
                answer_text=answer_text, points=grade.points,
                max_points=grade.max_points, score=grade.score,
                feedback=grade.feedback,
                checks=[check.model_dump() for check in grade.checks],
            ))
            session.flush()


def get_attempts(student_id: int) -> list[dict]:
    """Every answer a student has given, newest first."""
    with get_session() as session:
        rows = session.execute(
            select(Attempt, QuestionRow, Document)
            .select_from(Attempt)
            .join(QuestionRow, Attempt.question_id == QuestionRow.id)
            .join(Document, QuestionRow.document_id == Document.id)
            .where(Attempt.student_id == student_id, Document.owner_id == student_id)
            .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        ).all()
        return [
            {
                "created_at": attempt.created_at,
                "pdf": doc.title,
                "quiz_no": question.quiz_no,
                "type": question.type,
                "difficulty": question.difficulty,
                "question": question.question,
                "answer_text": attempt.answer_text or "",
                "points": attempt.points,
                "max_points": attempt.max_points,
                "feedback": attempt.feedback,
            }
            for attempt, question, doc in rows
        ]


def get_quiz_summary(student_id: int) -> list[dict]:
    """One row per quiz: total points and maximum points."""
    with get_session() as session:
        rows = session.execute(
            select(
                Document.title,
                QuestionRow.quiz_no,
                func.count(Attempt.id),
                func.sum(Attempt.points),
                func.sum(Attempt.max_points),
                func.max(Attempt.created_at),
            )
            .select_from(Attempt)
            .join(QuestionRow, Attempt.question_id == QuestionRow.id)
            .join(Document, QuestionRow.document_id == Document.id)
            .where(Attempt.student_id == student_id, Document.owner_id == student_id)
            .group_by(Document.id, QuestionRow.quiz_no)
            .order_by(func.max(Attempt.created_at).desc())
        ).all()
        return [
            {
                "pdf": title,
                "quiz_no": quiz_no,
                "questions": n_questions,
                "points": int(points or 0),
                "max_points": int(max_points or 0),
                "date": last,
            }
            for title, quiz_no, n_questions, points, max_points, last in rows
        ]

def require_document(session, doc_id, owner_id):
    doc = session.get(Document, doc_id)
    if owner_id is None or doc is None or doc.owner_id != owner_id:
        raise PermissionError("Document unavailable")
    return doc


def verify_document_owner(doc_id: int, student_id: int) -> None:
    with get_session() as session:
        require_document(session, doc_id, student_id)


def load_chat(student_id, doc_id):
    with get_session() as session:
        require_document(session, doc_id, student_id)
        row = session.get(Conversation, (student_id, doc_id))
        return row.messages if row else []


def save_chat(student_id, doc_id, messages):
    with get_session() as session:
        require_document(session, doc_id, student_id)
        session.merge(Conversation(student_id=student_id, document_id=doc_id, messages=messages))
