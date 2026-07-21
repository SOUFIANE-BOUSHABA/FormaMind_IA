from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AssessmentDifficulty = Literal["beginner", "intermediate", "advanced", "adaptive"]
AssessmentSort = Literal["newest", "oldest"]
AssessmentStatus = Literal["generated", "in_progress", "completed"]
QuestionType = Literal[
    "multiple_choice",
    "true_false",
    "short_answer",
    "explanation",
]


class GenerateAssessmentRequest(BaseModel):
    document_ids: list[int] = Field(min_length=1)
    title: str | None = Field(default=None, max_length=180)
    topics: list[str] = Field(min_length=1, max_length=5)
    difficulty: AssessmentDifficulty
    question_count: int = Field(ge=3, le=20)
    question_types: list[QuestionType] = Field(min_length=1)

    @field_validator("document_ids")
    @classmethod
    def reject_duplicate_document_ids(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            msg = "Duplicate document IDs are not allowed."
            raise ValueError(msg)
        return value

    @field_validator("topics")
    @classmethod
    def clean_topics(cls, value: list[str]) -> list[str]:
        cleaned_topics = [topic.strip() for topic in value if topic.strip()]
        if not cleaned_topics:
            msg = "At least one topic is required."
            raise ValueError(msg)

        if len(cleaned_topics) != len(set(topic.lower() for topic in cleaned_topics)):
            msg = "Duplicate topics are not allowed."
            raise ValueError(msg)

        return cleaned_topics

    @field_validator("question_types")
    @classmethod
    def reject_duplicate_question_types(
        cls,
        value: list[QuestionType],
    ) -> list[QuestionType]:
        if len(value) != len(set(value)):
            msg = "Duplicate question types are not allowed."
            raise ValueError(msg)
        return value

    @field_validator("title")
    @classmethod
    def clean_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned_title = value.strip()
        return cleaned_title or None


class GeneratedOptionDraft(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    is_correct: bool


class GeneratedQuestionDraft(BaseModel):
    type: QuestionType
    text: str = Field(min_length=1, max_length=2000)
    options: list[GeneratedOptionDraft] = Field(default_factory=list)
    correct_answer: str = Field(min_length=1, max_length=2000)
    explanation: str = Field(min_length=1, max_length=3000)
    points: int = Field(default=1, ge=1, le=10)
    source_ref: str = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_options_for_type(self) -> GeneratedQuestionDraft:
        if self.type == "multiple_choice":
            if len(self.options) != 4:
                msg = "Multiple-choice questions must have exactly 4 options."
                raise ValueError(msg)

            correct_options = [option for option in self.options if option.is_correct]
            if len(correct_options) != 1:
                msg = "Multiple-choice questions must have exactly one correct option."
                raise ValueError(msg)

            if self.correct_answer.strip() != correct_options[0].text.strip():
                msg = "Correct answer must match the correct option."
                raise ValueError(msg)

        elif self.type == "true_false":
            option_texts = [option.text.strip().lower() for option in self.options]
            if option_texts != ["vrai", "faux"]:
                msg = "True/false questions must have options: Vrai, Faux."
                raise ValueError(msg)

            correct_options = [option for option in self.options if option.is_correct]
            if len(correct_options) != 1:
                msg = "True/false questions must have exactly one correct option."
                raise ValueError(msg)

            if self.correct_answer.strip().lower() != correct_options[0].text.lower():
                msg = "Correct answer must match the correct true/false option."
                raise ValueError(msg)

        elif self.options:
            msg = "Short-answer and explanation questions must not have options."
            raise ValueError(msg)

        return self


class AssessmentDraft(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    difficulty: AssessmentDifficulty
    questions: list[GeneratedQuestionDraft] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return value.strip()


class PublicAssessmentDocument(BaseModel):
    id: int
    title: str
    page_count: int

    model_config = ConfigDict(from_attributes=True)


class PublicQuestionOption(BaseModel):
    id: int
    text: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class PublicQuestion(BaseModel):
    id: int
    type: QuestionType
    text: str
    points: int
    order_index: int
    source_document_id: int
    source_document_title: str
    source_page_number: int
    source_excerpt: str
    options: list[PublicQuestionOption]

    model_config = ConfigDict(from_attributes=True)


class AssessmentSummary(BaseModel):
    id: int
    title: str
    difficulty: AssessmentDifficulty
    status: AssessmentStatus
    question_count: int
    created_at: str
    updated_at: str


class AssessmentListResponse(BaseModel):
    items: list[AssessmentSummary]
    page: int
    page_size: int
    total: int
    total_pages: int


class AssessmentRead(BaseModel):
    id: int
    title: str
    difficulty: AssessmentDifficulty
    status: AssessmentStatus
    question_count: int
    created_at: str
    updated_at: str
    documents: list[PublicAssessmentDocument]
    questions: list[PublicQuestion]