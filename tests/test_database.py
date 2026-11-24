"""Database tests run on a temporary SQLite file, never on your real data."""
import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from db import database, queries  # noqa: E402
from db.tables import Base  # noqa: E402
from models.schemas import GradeResult, Question, RubricCheck  # noqa: E402


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    Base.metadata.create_all(engine)


def question(text):
    return Question(topic="t", difficulty="easy", type="short", question=text,
                    answer="a", rubric=["a", "b"], source_page=1)


def grade(points):
    return GradeResult(points=points, max_points=2, score=points / 2,
                       checks=[RubricCheck(point="a", covered=True)], feedback="fb")


def test_student_is_created_once():
    assert queries.get_or_create_student("Mali") == queries.get_or_create_student("Mali")


def test_documents_marks_and_delete():
    student = queries.get_or_create_student("Mali")
    doc_id = queries.add_document("Lecture 4", "lecture4.pdf", "hash1", 10, student)
    assert queries.get_document_by_hash("hash1", student)["id"] == doc_id
    assert queries.next_quiz_no(doc_id, student) == 1

    ids = queries.save_questions(doc_id, 1, [question("Q1?"), question("Q2?")], student)
    assert queries.next_quiz_no(doc_id, student) == 2
    queries.save_attempt(student, ids[0], "my answer", grade(2))
    queries.save_attempt(student, ids[1], "other", grade(1))

    summary = queries.get_quiz_summary(student)
    assert len(summary) == 1
    assert (summary[0]["points"], summary[0]["max_points"], summary[0]["questions"]) == (3, 4, 2)
    assert len(queries.get_attempts(student)) == 2

    queries.delete_document(doc_id, student)
    assert queries.list_documents(student) == []
    assert queries.get_attempts(student) == []