from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DashboardMetric(BaseModel):
    label: str
    value: str
    description: str
    icon: str
    tone: Literal["primary", "secondary", "accent", "success", "warning", "error"]
    trend: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)


class SkillMetric(BaseModel):
    label: str
    value: int = Field(ge=0, le=100)
    highlighted: bool = False


class AgentActivity(BaseModel):
    name: str
    status: Literal["online", "active", "waiting"]
    description: str
    tone: Literal["primary", "secondary", "accent"]


class Recommendation(BaseModel):
    eyebrow: str
    title: str
    duration: str
    badge: str
    description: str
    action_label: str


class FocusArea(BaseModel):
    label: str
    severity: Literal["critical", "important"]
    progress: int = Field(ge=0, le=100)


class ActivityEntry(BaseModel):
    title: str
    description: str
    timestamp: str
    tone: Literal["primary", "secondary", "accent"]


class DashboardSummary(BaseModel):
    learner_name: str
    learner_title: str
    greeting: str
    subtitle: str
    metrics: list[DashboardMetric]
    skills: list[SkillMetric]
    agents: list[AgentActivity]
    recommendation: Recommendation | None
    focus_areas: list[FocusArea]
    recent_activity: list[ActivityEntry]
