import pytest

from core import config, llm_client, question_gen, teacher
from models.schemas import Question, QuestionSet


def test_parse_json_handles_code_fences_and_extra_text():
    assert llm_client._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm_client._parse_json('Sure! Here it is: {"a": 2} Hope that helps.') == {"a": 2}
    with pytest.raises(ValueError):
        llm_client._parse_json("no json here")


def test_chat_validated_retries_after_invalid_json(monkeypatch):
    replies = iter(["not json at all", '{"questions": []}', GOOD_JSON])
    calls = []

    def fake_raw(messages, temperature, schema, max_tokens=None):
        calls.append(messages)
        assert schema is not None  # the JSON schema is sent to Ollama
        return next(replies)

    monkeypatch.setattr(llm_client, "_chat_raw", fake_raw)
    result = llm_client.chat_validated([{"role": "user", "content": "go"}], QuestionSet)
    assert len(result.questions) == 1
    assert len(calls) == 3
    assert "did not match" in calls[-1][-1]["content"]


def test_chat_validated_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(llm_client, "_chat_raw", lambda m, t, s, **kwargs: "nope")
    with pytest.raises(RuntimeError):
        llm_client.chat_validated([{"role": "user", "content": "go"}], QuestionSet, retries=1)


GOOD_JSON = (
    '{"questions": [{"topic": "GD", "difficulty": "Easy", "type": "short", '
    '"question": "What is a learning rate?", "answer": "The step size.", '
    '"rubric": ["step size"], "source_page": 2}]}'
)


def test_missing_model_gives_clear_error(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_MODEL", "")
    ok, message = llm_client.check_ollama()
    assert not ok and "OLLAMA_MODEL" in message


def test_render_prompt_does_not_reexpand_text_inside_values():
    text = config.render_prompt("grader", question="Q {student_answer}", reference_answer="R",
                                rubric="1. x", student_answer="S")
    assert "Q {student_answer}" in text


def test_clean_answer_replaces_not_in_pdf_signal():
    assert teacher.clean_answer("NOT_IN_PDF") == teacher.NOT_FOUND_MESSAGE
    assert teacher.clean_answer(" Hello [p.2] ") == "Hello [p.2]"


def test_select_chunks_spreads_and_keeps_reading_order():
    chunks = [{"text": "x" * 100, "page": i, "section": "S", "chunk_index": i} for i in range(10)]
    picked = question_gen.select_chunks(chunks, 5)
    assert len(picked) == 5
    assert [c["chunk_index"] for c in picked] == sorted(c["chunk_index"] for c in picked)


def test_clean_questions_fixes_page_and_removes_duplicates_and_wrong_types():
    def q(text, page=99, kind="short"):
        return Question(topic="t", difficulty="easy", type=kind, question=text,
                        answer="a", rubric=["a"], source_page=page)

    cleaned = question_gen.clean_questions(
        [q("One?"), q("one?"), q("Two?", page=4), q("Three?", kind="exercise")],
        allowed_pages={4, 5}, allowed_types={"short"}, n=5,
    )
    assert [x.question for x in cleaned] == ["Two?"]
    assert cleaned[0].source_page == 4  # Invalid source page is rejected