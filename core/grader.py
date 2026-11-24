"""Rubric-based grading.

The LLM only decides, for each rubric point, "covered: true/false" and writes
feedback. The score itself is calculated here in Python (points covered /
total points), so the marks are consistent and easy to explain.
"""
from __future__ import annotations

from core import config, llm_client
from models.schemas import GradeResult, Question, RubricCheck, RubricJudgement


def compute_grade(rubric: list[str], judgement: RubricJudgement) -> GradeResult:
    """Turn the LLM's yes/no checks into a GradeResult (pure function)."""
    checks: list[RubricCheck] = []
    for index, point in enumerate(rubric):
        covered = bool(judgement.checks[index].covered) if index < len(judgement.checks) else False
        checks.append(RubricCheck(point=point, covered=covered))
    max_points = max(len(rubric), 1)
    points = sum(1 for check in checks if check.covered)
    return GradeResult(
        points=points,
        max_points=max_points,
        score=points / max_points,
        checks=checks,
        feedback=judgement.feedback.strip(),
    )


def grade_mcq(question: Question, chosen: str | None) -> GradeResult:
    """Multiple choice is marked automatically (no LLM needed)."""
    correct = chosen is not None and chosen.strip() == question.answer.strip()
    feedback = "Correct!" if correct else f"Not quite. The correct answer is: {question.answer}"
    return GradeResult(
        points=1 if correct else 0,
        max_points=1,
        score=1.0 if correct else 0.0,
        checks=[RubricCheck(point="Chooses the correct option", covered=correct)],
        feedback=feedback,
    )


def grade_open(question: Question, student_answer: str) -> GradeResult:
    """Short answers and exercises are marked against the rubric by the LLM."""
    if not student_answer.strip():
        checks = [RubricCheck(point=point, covered=False) for point in question.rubric]
        return GradeResult(
            points=0,
            max_points=max(len(question.rubric), 1),
            score=0.0,
            checks=checks,
            feedback="No answer was given.",
        )
    rubric_text = "\n".join(f"{i}. {point}" for i, point in enumerate(question.rubric, start=1))
    prompt = config.render_prompt(
        "grader",
        question=question.question,
        reference_answer=question.answer,
        rubric=rubric_text,
        student_answer=student_answer.strip(),
    )
    judgement = llm_client.chat_validated(
        [{"role": "user", "content": prompt}],
        RubricJudgement,
        temperature=config.TEMP_JSON,
    )
    return compute_grade(question.rubric, judgement)


def grade(question: Question, student_answer: str | None) -> GradeResult:
    if question.type == "mcq":
        return grade_mcq(question, student_answer)
    return grade_open(question, student_answer or "")