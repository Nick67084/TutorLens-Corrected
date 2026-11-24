
"""Database tables (SQLite through SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ======================================
# STUDENTS
# ======================================

class Student(Base):

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100), unique=True
    )


# ======================================
# STUDENT ACCOUNTS
# ======================================

class Account(Base):

    __tablename__ = "accounts"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        primary_key=True,
    )

    login_id: Mapped[str] = mapped_column(
        String(64), unique=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100)
    )

    password_hash: Mapped[str] = mapped_column(
        Text
    )


# ======================================
# CONVERSATION HISTORY
# ======================================

class Conversation(Base):

    __tablename__ = "conversations"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        primary_key=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        primary_key=True,
    )

    messages: Mapped[list] = mapped_column(
        JSON, default=list
    )


# ======================================
# COURSE DOCUMENTS
# ======================================

class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("students.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    filename: Mapped[str] = mapped_column(
        String(255)
    )

    file_hash: Mapped[str] = mapped_column(
        String(64), index=True
    )

    n_pages: Mapped[int] = mapped_column(
        Integer
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
    )


# ======================================
# QUIZ QUESTIONS
# ======================================

class QuestionRow(Base):

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id")
    )

    quiz_no: Mapped[int] = mapped_column(Integer)

    topic: Mapped[str] = mapped_column(String(255))

    difficulty: Mapped[str] = mapped_column(String(20))

    type: Mapped[str] = mapped_column(String(20))

    question: Mapped[str] = mapped_column(Text)

    options: Mapped[list] = mapped_column(
        JSON, default=list
    )

    answer: Mapped[str] = mapped_column(Text)

    rubric: Mapped[list] = mapped_column(
        JSON, default=list
    )

    source_page: Mapped[int] = mapped_column(
        Integer, default=1
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
    )


# ======================================
# QUIZ ATTEMPTS AND MARKS
# ======================================

class Attempt(Base):

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id")
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id")
    )

    answer_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    points: Mapped[int] = mapped_column(Integer)

    max_points: Mapped[int] = mapped_column(Integer)

    score: Mapped[float] = mapped_column(Float)

    feedback: Mapped[str] = mapped_column(
        Text, default=""
    )

    checks: Mapped[list] = mapped_column(
        JSON, default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
    )
