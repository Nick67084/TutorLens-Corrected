from core import grader
from models.schemas import Question, RubricCheck, RubricJudgement


def open_question():
    return Question(
        topic="Gradient descent",
        difficulty="medium",
        type="short",
        question="Why does gradient descent need a learning rate?",
        answer="It sets the step size.",
        rubric=["Step size", "Weight updates", "Too small is slow", "Too large overshoots"],
        source_page=7,
    )


def test_compute_grade_counts_covered_points():
    judgement = RubricJudgement(
        checks=[RubricCheck(point=p, covered=c) for p, c in
                [("a", True), ("b", True), ("c", True), ("d", False)]],
        feedback="  Good start.  ",
    )
    result = grader.compute_grade(open_question().rubric, judgement)
    assert (result.points, result.max_points) == (3, 4)
    assert result.score == 0.75
    assert result.feedback == "Good start."
    assert result.missing_points == ["Too large overshoots"]


def test_compute_grade_treats_missing_checks_as_not_covered():
    judgement = RubricJudgement(checks=[RubricCheck(point="a", covered=True)], feedback="ok")
    result = grader.compute_grade(open_question().rubric, judgement)
    assert result.points == 1
    assert len(result.checks) == 4


def test_mcq_is_marked_without_the_llm():
    q = Question(
        topic="t", difficulty="easy", type="mcq", question="Q?",
        options=["A1", "B1", "C1"], answer="B1", source_page=1,
    )
    assert grader.grade(q, "B1").points == 1
    wrong = grader.grade(q, "A1")
    assert wrong.points == 0 and "B1" in wrong.feedback
    assert grader.grade(q, None).points == 0


def test_empty_open_answer_scores_zero_without_the_llm():
    result = grader.grade(open_question(), "   ")
    assert result.points == 0
    assert result.max_points == 4


def test_open_answer_uses_the_llm_judgement(monkeypatch):
    def fake_chat_validated(messages, model_cls, temperature=None, retries=2):
        assert "learning rate" in messages[0]["content"]
        return RubricJudgement(
            checks=[RubricCheck(point="x", covered=value) for value in (True, True, False, False)],
            feedback="Add what happens when the rate is too large.",
        )

    monkeypatch.setattr(grader.llm_client, "chat_validated", fake_chat_validated)
    result = grader.grade(open_question(), "It controls how big each step is.")
    assert (result.points, result.max_points) == (2, 4)