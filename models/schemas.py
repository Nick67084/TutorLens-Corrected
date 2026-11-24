"""Pydantic data models shared by the whole app."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Difficulty = Literal["easy", "medium", "hard"]
QuestionType = Literal["mcq", "short", "exercise"]


class Question(BaseModel):
    topic: str
    difficulty: Difficulty
    type: QuestionType
    question: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)  # only used for mcq
    answer: str = Field(min_length=1)
    rubric: list[str] = Field(default_factory=list)   # points a good answer must cover
    source_page: int = 1

    @field_validator("difficulty", "type", mode="before")
    @classmethod
    def _lowercase(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _check_consistency(self):
        if self.type == "mcq":
            if len(self.options) < 2:
                raise ValueError("an mcq question needs at least 2 options")
            # the answer must be one of the options (accept "B" or "b" as a letter)
            matched = None
            answer = self.answer.strip()
            for option in self.options:
                if option.strip().lower() == answer.lower():
                    matched = option
                    break
            if matched is None and len(answer) == 1 and answer.upper() in "ABCDEF":
                index = "ABCDEF".index(answer.upper())
                if index < len(self.options):
                    matched = self.options[index]
            if matched is None:
                raise ValueError("the mcq answer must be exactly one of the options")
            self.answer = matched
            if not self.rubric:
                self.rubric = ["Chooses the correct option"]
        elif not self.rubric:
            self.rubric = [self.answer]
        return self


class QuestionSet(BaseModel):
    questions: list[Question] = Field(min_length=1)


class RubricCheck(BaseModel):
    point: str
    covered: bool


class RubricJudgement(BaseModel):
    """What the LLM returns when it marks an answer."""

    checks: list[RubricCheck]
    feedback: str


class GradeResult(BaseModel):
    """The final mark that the app shows and stores."""

    points: int
    max_points: int
    score: float  # points / max_points, between 0 and 1
    checks: list[RubricCheck]
    feedback: str

    @property
    def missing_points(self) -> list[str]:
        return [check.point for check in self.checks if not check.covered]