from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

SoutenanceAnswerStatus = Literal["waiting", "answered"]
SoutenanceCategory = Literal[
    "technical",
    "architecture",
    "ai_concepts",
    "security",
    "project_choices",
    "limitations",
    "testing",
    "deployment",
    "jury_challenge",
]
SoutenanceDifficulty = Literal["beginner", "intermediate", "advanced", "adaptive"]
SoutenanceMode = Literal["training", "jury"]
SoutenanceSessionStatus = Literal["in_progress", "completed"]

RUBRIC_CRITERIA = [
    "technical_accuracy",
    "clarity",
    "structure",
    "architecture",
    "choice_justification",
    "security_limitations",
    "communication",
]

CATEGORY_LABELS: dict[str, str] = {
    "ai_concepts": "Concepts IA",
    "architecture": "Architecture",
    "deployment": "Deploiement",
    "jury_challenge": "Question piege du jury",
    "limitations": "Limites",
    "project_choices": "Choix du projet",
    "security": "Securite",
    "technical": "Technique",
    "testing": "Tests",
}


class CreateSoutenanceSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=180)
    mode: SoutenanceMode
    difficulty: SoutenanceDifficulty
    question_count: int = Field(ge=3, le=20)
    question_categories: list[SoutenanceCategory] = Field(min_length=1, max_length=9)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("question_categories")
    @classmethod
    def reject_duplicate_categories(
        cls,
        value: list[SoutenanceCategory],
    ) -> list[SoutenanceCategory]:
        if len(value) != len(set(value)):
            msg = "Duplicate question categories are not allowed."
            raise ValueError(msg)
        return value


class SoutenanceQuestionDraft(BaseModel):
    local_id: str = Field(min_length=1, max_length=60)
    text: str = Field(min_length=1, max_length=900)
    category: SoutenanceCategory
    difficulty: SoutenanceDifficulty
    expected_concepts: list[str] = Field(min_length=1, max_length=8)
    evaluation_focus: str = Field(min_length=1, max_length=1000)
    follow_up_hint: str = Field(min_length=1, max_length=700)
    order_index: int = Field(ge=0)

    @field_validator("expected_concepts")
    @classmethod
    def clean_concepts(cls, value: list[str]) -> list[str]:
        cleaned = [" ".join(item.split()) for item in value if item.strip()]
        if not cleaned:
            msg = "At least one expected concept is required."
            raise ValueError(msg)
        return cleaned


class SoutenanceSessionDraft(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    introduction: str = Field(min_length=1, max_length=1200)
    questions: list[SoutenanceQuestionDraft] = Field(min_length=1)


class SoutenanceRubricScoreDraft(BaseModel):
    criterion: str = Field(min_length=1, max_length=80)
    score: float = Field(ge=0, le=100)
    comment: str = Field(min_length=1, max_length=700)


class SoutenanceAnswerEvaluationDraft(BaseModel):
    question_id: int = Field(gt=0)
    rubric_scores: list[SoutenanceRubricScoreDraft] = Field(min_length=1)
    feedback: str = Field(min_length=1, max_length=1600)
    strengths: list[str] = Field(default_factory=list, max_length=8)
    missing_concepts: list[str] = Field(default_factory=list, max_length=8)
    improved_answer: str = Field(min_length=1, max_length=2000)
    recommendation: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def reject_duplicate_criteria(self) -> SoutenanceAnswerEvaluationDraft:
        criteria = [item.criterion for item in self.rubric_scores]
        if len(criteria) != len(set(criteria)):
            msg = "Duplicate rubric criteria are not allowed."
            raise ValueError(msg)
        return self


class SoutenanceRubricCriterionRead(BaseModel):
    criterion: str
    label: str
    weight: int
    score: float
    comment: str


class SoutenanceAnswerFeedback(BaseModel):
    total_score: float
    feedback: str
    strengths: list[str]
    missing_concepts: list[str]
    improved_answer: str
    recommendation: str
    rubric_scores: list[SoutenanceRubricCriterionRead]


class PublicSoutenanceQuestion(BaseModel):
    id: int
    text: str
    category: SoutenanceCategory
    category_label: str
    difficulty: SoutenanceDifficulty
    order_index: int
    answer_status: SoutenanceAnswerStatus


class SoutenanceCurrentQuestionResponse(BaseModel):
    session_id: int
    status: SoutenanceSessionStatus
    mode: SoutenanceMode
    question_index: int
    total_questions: int
    progress_percentage: int
    question: PublicSoutenanceQuestion | None


class SubmitSoutenanceAnswerRequest(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=6000)

    @field_validator("answer")
    @classmethod
    def clean_answer(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            msg = "Saisissez une reponse avant de continuer."
            raise ValueError(msg)
        return cleaned


class SubmitSoutenanceAnswerResponse(BaseModel):
    session_id: int
    question_id: int
    mode: SoutenanceMode
    status: SoutenanceSessionStatus
    feedback: SoutenanceAnswerFeedback | None
    next_question: PublicSoutenanceQuestion | None
    progress_percentage: int
    message: str


class SoutenanceSessionListItem(BaseModel):
    id: int
    title: str
    mode: SoutenanceMode
    difficulty: SoutenanceDifficulty
    status: SoutenanceSessionStatus
    question_count: int
    answered_count: int
    progress_percentage: int
    final_score: float | None
    readiness_level: str | None
    created_at: str
    completed_at: str | None


class SoutenanceSessionListResponse(BaseModel):
    items: list[SoutenanceSessionListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class SoutenanceSessionRead(BaseModel):
    id: int
    title: str
    introduction: str
    mode: SoutenanceMode
    difficulty: SoutenanceDifficulty
    status: SoutenanceSessionStatus
    question_count: int
    answered_count: int
    current_question_index: int
    progress_percentage: int
    final_score: float | None
    readiness_level: str | None
    created_at: str
    completed_at: str | None
    questions: list[PublicSoutenanceQuestion]


class SoutenanceQuestionResult(BaseModel):
    question: PublicSoutenanceQuestion
    answer_text: str
    feedback: SoutenanceAnswerFeedback


class SoutenanceCategoryScore(BaseModel):
    category: SoutenanceCategory
    category_label: str
    score: float
    answered_count: int


class SoutenanceResultsResponse(BaseModel):
    id: int
    title: str
    mode: SoutenanceMode
    difficulty: SoutenanceDifficulty
    final_score: float
    readiness_level: str
    strengths: list[str]
    weaknesses: list[str]
    missing_concepts: list[str]
    recommendations: list[str]
    category_scores: list[SoutenanceCategoryScore]
    questions: list[SoutenanceQuestionResult]
    completed_at: str


class ProjectContextSnapshot(BaseModel):
    project_objective: str
    backend_stack: list[str] = Field(default_factory=list)
    frontend_stack: list[str] = Field(default_factory=list)
    database: str
    implemented_features: list[str] = Field(default_factory=list)
    endpoints: list[str] = Field(default_factory=list)
    security_boundaries: list[str] = Field(default_factory=list)
    known_limits: list[str] = Field(default_factory=list)


class LearnerProfileSnapshot(BaseModel):
    learner_name: str
    global_score: float
    current_level: str
    recent_assessment_scores: list[float] = Field(default_factory=list)
    weak_topics: list[str] = Field(default_factory=list)
    strong_topics: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    learning_plan_progress: list[int] = Field(default_factory=list)
    previous_soutenance_scores: list[float] = Field(default_factory=list)
    previous_soutenance_weaknesses: list[str] = Field(default_factory=list)
