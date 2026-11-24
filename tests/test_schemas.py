import pytest
from pydantic import ValidationError

from models.schemas import GradeResult, Question, QuestionSet, RubricCheck


def make_mcq(**overrides):
    data = dict(
        topic="Gradient descent",
        difficulty="easy",
        type="mcq",
        question="What does the learning rate control?",
        options=["Step size", "Number of layers", "Dataset size", "Batch name"],
        answer="Step size",
        rubric=[],
        source_page=3,
    )
    data.update(overrides)
    return Question(**data)


def test_mcq_gets_default_rubric():
    q = make_mcq()
    assert q.rubric == ["Chooses the correct option"]


def test_mcq_answer_given_as_letter_is_matched_to_option():
    q = make_mcq(answer="a")
    assert q.answer == "Step size"


def test_mcq_answer_must_be_one_of_the_options():
    with pytest.raises(ValidationError):
        make_mcq(answer="Something else")


def test_mcq_needs_two_options():
    with pytest.raises(ValidationError):
        make_mcq(options=["Step size"])


def test_difficulty_and_type_are_lowercased():
    q = make_mcq(difficulty="Medium", type="MCQ")
    assert q.difficulty == "medium"
    assert q.type == "mcq"


def test_short_question_without_rubric_uses_answer_as_rubric():
    q = Question(
        topic="Overfitting",
        difficulty="medium",
        type="short",
        question="What is overfitting?",
        answer="The model learns noise in the training data.",
        source_page=5,
    )
    assert q.rubric == ["The model learns noise in the training data."]


def test_question_set_cannot_be_empty():
    with pytest.raises(ValidationError):
        QuestionSet(questions=[])


def test_grade_result_lists_missing_points():
    grade = GradeResult(
        points=1,
        max_points=2,
        score=0.5,
        checks=[RubricCheck(point="A", covered=True), RubricCheck(point="B", covered=False)],
        feedback="ok",
    )
    assert grade.missing_points == ["B"]