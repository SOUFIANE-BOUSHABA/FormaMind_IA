from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.assessment import AssessmentAttempt
    from app.models.document import Document
    from app.models.user import User

LearningActivityStatus = Literal["pending", "in_progress", "completed"]
LearningActivityType = Literal["review", "practice", "quiz", "reflection"]
LearningModulePriority = Literal["high", "medium", "low"]
LearningPlanIntensity = Literal["light", "balanced", "intensive"]
LearningPlanStatus = Literal["active", "completed"]


class LearningPlan(Base):
    __tablename__ = "learning_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed')",
            name="ck_learning_plans_status",
        ),
        CheckConstraint(
            "intensity IN ('light', 'balanced', 'intensive')",
            name="ck_learning_plans_intensity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24),
        default="active",
        index=True,
        nullable=False,
    )
    intensity: Mapped[str] = mapped_column(String(24), nullable=False)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="learning_plans")
    attempt: Mapped[AssessmentAttempt] = relationship(
        "AssessmentAttempt",
        back_populates="learning_plans",
    )
    modules: Mapped[list[LearningModule]] = relationship(
        "LearningModule",
        back_populates="plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LearningModule.order_index",
    )


class LearningModule(Base):
    __tablename__ = "learning_modules"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('high', 'medium', 'low')",
            name="ck_learning_modules_priority",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(180), nullable=False)
    priority: Mapped[str] = mapped_column(String(24), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    plan: Mapped[LearningPlan] = relationship(
        "LearningPlan",
        back_populates="modules",
    )
    activities: Mapped[list[LearningActivity]] = relationship(
        "LearningActivity",
        back_populates="module",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LearningActivity.order_index",
    )


class LearningActivity(Base):
    __tablename__ = "learning_activities"
    __table_args__ = (
        CheckConstraint(
            "type IN ('review', 'practice', 'quiz', 'reflection')",
            name="ck_learning_activities_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed')",
            name="ck_learning_activities_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24),
        default="pending",
        index=True,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    module: Mapped[LearningModule] = relationship(
        "LearningModule",
        back_populates="activities",
    )
    sources: Mapped[list[LearningActivitySource]] = relationship(
        "LearningActivitySource",
        back_populates="activity",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LearningActivitySource.id",
    )


class LearningActivitySource(Base):
    __tablename__ = "learning_activity_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("learning_activities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    activity: Mapped[LearningActivity] = relationship(
        "LearningActivity",
        back_populates="sources",
    )
    document: Mapped[Document] = relationship("Document")
