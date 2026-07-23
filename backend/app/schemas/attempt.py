from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.assessment import AssessmentDifficulty, QuestionType

AttemptStatus = Literal["in_progress", "evaluating", "evaluated"]
AnswerEvaluationStatus = Literal["correct", "partial", "incorrect", "unanswered"]
AssessmentMasteryLevel = Literal["weak", "medium", "strong"]


class StartAttemptResponse(BaseModel):
    id: int
    assessment_id: int
    status: AttemptStatus
    started_at: str
    answered_count: int
    total_questions: int


class AttemptAnswerSaveRequest(BaseModel):
    selected_option_id: int | None = None
    text_answer: str | None = Field(default=None, max_length=4000)
    is_flagged: bool = False

    @field_validator("text_answer")
    @classmethod
    def clean_text_answer(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class PublicAttemptAnswer(BaseModel):
    question_id: int
    selected_option_id: int | None
    text_answer: str | None
    is_flagged: bool
    evaluation_status: AnswerEvaluationStatus | None = None
    is_correct: bool | None = None
    points_awarded: float | None = None
    feedback: str | None = None
    missing_concepts: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AttemptQuestionOption(BaseModel):
    id: int
    text: str
    order_index: int


class AttemptQuestion(BaseModel):
    id: int
    type: QuestionType
    text: str
    points: int
    order_index: int
    options: list[AttemptQuestionOption]


class AttemptDetailResponse(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    difficulty: AssessmentDifficulty
    status: AttemptStatus
    started_at: str
    submitted_at: str | None
    evaluated_at: str | None
    answered_count: int
    flagged_count: int
    total_questions: int
    questions: list[AttemptQuestion]
    answers: list[PublicAttemptAnswer]


class AttemptHistoryItem(BaseModel):
    id: int
    assessment_id: int
    status: AttemptStatus
    score: float | None
    max_score: float | None
    percentage: float | None
    level: str | None
    started_at: str
    submitted_at: str | None
    evaluated_at: str | None
    answered_count: int
    total_questions: int


class AttemptListResponse(BaseModel):
    items: list[AttemptHistoryItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class ResultQuestionOption(BaseModel):
    id: int
    text: str
    order_index: int
    is_correct: bool


class ResultQuestion(BaseModel):
    id: int
    type: QuestionType
    text: str
    points: int
    order_index: int
    correct_answer: str
    explanation: str
    source_document_id: int
    source_document_title: str
    source_page_number: int
    source_excerpt: str
    options: list[ResultQuestionOption]
    learner_answer: PublicAttemptAnswer


class AssessmentCoachSource(BaseModel):
    document_id: int
    document_title: str
    page_number: int = Field(ge=1)
    excerpt: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=400)


class AssessmentCoachFeedback(BaseModel):
    score_percent: float
    mastery_level: AssessmentMasteryLevel
    summary: str = Field(min_length=1, max_length=1200)
    points_a_renforcer: list[str] = Field(default_factory=list, max_length=8)
    points_acquis: list[str] = Field(default_factory=list, max_length=8)
    recommended_actions: list[str] = Field(default_factory=list, max_length=8)
    recommended_sources: list[AssessmentCoachSource] = Field(
        default_factory=list,
        max_length=8,
    )
    confidence: str = "medium"
    refusal_reason: str | None = None


class AssessmentCoachQuestionInput(BaseModel):
    question_id: int
    question_text: str
    expected_answer: str
    explanation: str
    points: float
    points_awarded: float
    evaluation_status: AnswerEvaluationStatus
    feedback: str | None = None
    missing_concepts: list[str] = Field(default_factory=list)
    source_document_id: int
    source_document_title: str
    source_page_number: int
    source_excerpt: str


class AssessmentCoachState(BaseModel):
    selected_task: Literal["analyze_attempt", "recommend_reinforcement"]
    learner_score: float
    mastery_level: AssessmentMasteryLevel
    weak_points: list[str] = Field(default_factory=list)
    mastered_points: list[str] = Field(default_factory=list)
    recommended_source_ids: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    refusal_reason: str | None = None


class AttemptResultsResponse(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    difficulty: AssessmentDifficulty
    status: Literal["evaluated"]
    score: float
    max_score: float
    percentage: float
    level: str
    strong_topics: list[str]
    weak_topics: list[str]
    started_at: str
    submitted_at: str
    evaluated_at: str
    coach_feedback: AssessmentCoachFeedback | None = None
    questions: list[ResultQuestion]


class OpenAnswerEvaluationInput(BaseModel):
    question_id: int
    question_type: Literal["short_answer", "explanation"]
    question_text: str
    expected_answer: str
    rubric: str
    max_points: float = Field(gt=0)
    learner_answer: str
    source_excerpt: str
    topic: str | None = None


class OpenAnswerEvaluation(BaseModel):
    question_id: int
    points_awarded: float = Field(ge=0)
    evaluation_status: AnswerEvaluationStatus
    feedback: str = Field(min_length=1, max_length=1000)
    missing_concepts: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def normalize_status(self) -> OpenAnswerEvaluation:
        if self.evaluation_status == "unanswered" and self.points_awarded != 0:
            msg = "Unanswered evaluations must award zero points."
            raise ValueError(msg)
        return self


class OpenAnswerEvaluationBatch(BaseModel):
    evaluations: list[OpenAnswerEvaluation]
