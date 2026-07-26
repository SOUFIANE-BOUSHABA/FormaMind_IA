from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LearningActivityStatus = Literal["pending", "in_progress", "completed"]
LearningActivityType = Literal["review", "practice", "quiz", "reflection"]
LearningModulePriority = Literal["high", "medium", "low"]
LearningPlanIntensity = Literal["light", "balanced", "intensive"]
LearningPlanStatus = Literal["active", "completed"]


class GenerateLearningPlanRequest(BaseModel):
    attempt_id: int = Field(gt=0)
    title: str | None = Field(default=None, max_length=180)
    daily_minutes: int = Field(default=45, ge=15, le=240)
    start_date: date = Field(default_factory=date.today)
    intensity: LearningPlanIntensity = "balanced"

    @field_validator("title")
    @classmethod
    def clean_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def reject_unreasonable_start_date(self) -> GenerateLearningPlanRequest:
        oldest_allowed = date.today() - timedelta(days=7)
        if self.start_date < oldest_allowed:
            msg = "Start date is too far in the past."
            raise ValueError(msg)
        return self


class UpdateLearningActivityStatusRequest(BaseModel):
    status: LearningActivityStatus


class LearningSourceDraft(BaseModel):
    source_ref: str = Field(min_length=1, max_length=80)
    reason: str = Field(default="", max_length=400)


class LearningActivityDraft(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    instructions: str = Field(min_length=1, max_length=2000)
    type: LearningActivityType
    duration_minutes: int = Field(ge=5, le=240)
    source_refs: list[str] = Field(min_length=1, max_length=4)

    @field_validator("source_refs")
    @classmethod
    def unique_source_refs(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            msg = "Duplicate source refs are not allowed."
            raise ValueError(msg)
        return cleaned


class LearningModuleDraft(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    objective: str = Field(min_length=1, max_length=1200)
    topic: str = Field(min_length=1, max_length=180)
    priority: LearningModulePriority
    activities: list[LearningActivityDraft] = Field(min_length=1)


class LearningPlanDraft(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    generated_summary: str = Field(min_length=1, max_length=2000)
    modules: list[LearningModuleDraft] = Field(min_length=1)


class LearningPlanSource(BaseModel):
    document_id: int
    document_title: str
    page_number: int = Field(ge=1)
    excerpt: str


class LearningActivityRead(BaseModel):
    id: int
    title: str
    instructions: str
    type: LearningActivityType
    status: LearningActivityStatus
    order_index: int
    scheduled_date: str
    duration_minutes: int
    started_at: str | None
    completed_at: str | None
    sources: list[LearningPlanSource]


class LearningModuleRead(BaseModel):
    id: int
    title: str
    objective: str
    topic: str
    priority: LearningModulePriority
    order_index: int
    estimated_minutes: int
    activities: list[LearningActivityRead]


class LearningPlanRead(BaseModel):
    id: int
    attempt_id: int
    assessment_title: str
    title: str
    status: LearningPlanStatus
    intensity: LearningPlanIntensity
    daily_minutes: int
    start_date: str
    target_end_date: str
    progress_percentage: int
    generated_summary: str
    created_at: str
    updated_at: str
    modules: list[LearningModuleRead]


class LearningPlanListItem(BaseModel):
    id: int
    attempt_id: int
    assessment_title: str
    title: str
    status: LearningPlanStatus
    intensity: LearningPlanIntensity
    daily_minutes: int
    start_date: str
    target_end_date: str
    progress_percentage: int
    next_activity_title: str | None
    next_activity_date: str | None
    created_at: str


class LearningPlanListResponse(BaseModel):
    items: list[LearningPlanListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class AssessmentEvidenceItem(BaseModel):
    question_id: int
    question_text: str
    expected_answer: str
    learner_answer: str | None
    evaluation_status: str
    points: float
    points_awarded: float
    feedback: str | None
    missing_concepts: list[str] = Field(default_factory=list)
    source_document_id: int
    source_document_title: str
    source_page_number: int
    source_excerpt: str

    model_config = ConfigDict(from_attributes=True)


class AssessmentLearningSnapshot(BaseModel):
    attempt_id: int
    assessment_title: str
    score_percent: float
    level: str
    strong_topics: list[str] = Field(default_factory=list)
    weak_topics: list[str] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
    evidence: list[AssessmentEvidenceItem] = Field(default_factory=list)
