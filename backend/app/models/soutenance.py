from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.user import User

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


class SoutenanceSession(Base):
    __tablename__ = "soutenance_sessions"
    __table_args__ = (
        CheckConstraint(
            "mode IN ('training', 'jury')",
            name="ck_soutenance_sessions_mode",
        ),
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'adaptive')",
            name="ck_soutenance_sessions_difficulty",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'completed')",
            name="ck_soutenance_sessions_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    introduction: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24),
        default="in_progress",
        index=True,
        nullable=False,
    )
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    final_score: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    readiness_level: Mapped[str | None] = mapped_column(String(60), nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_concepts: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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

    user: Mapped[User] = relationship("User", back_populates="soutenance_sessions")
    questions: Mapped[list[SoutenanceQuestion]] = relationship(
        "SoutenanceQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SoutenanceQuestion.order_index",
    )


class SoutenanceQuestion(Base):
    __tablename__ = "soutenance_questions"
    __table_args__ = (
        CheckConstraint(
            (
                "category IN ('technical', 'architecture', 'ai_concepts', "
                "'security', 'project_choices', 'limitations', 'testing', "
                "'deployment', 'jury_challenge')"
            ),
            name="ck_soutenance_questions_category",
        ),
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'adaptive')",
            name="ck_soutenance_questions_difficulty",
        ),
        CheckConstraint(
            "answer_status IN ('waiting', 'answered')",
            name="ck_soutenance_questions_answer_status",
        ),
        UniqueConstraint(
            "session_id",
            "local_id",
            name="uq_soutenance_questions_session_local_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("soutenance_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    local_id: Mapped[str] = mapped_column(String(60), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), nullable=False)
    expected_concepts: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_focus: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_hint: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_status: Mapped[str] = mapped_column(
        String(24),
        default="waiting",
        index=True,
        nullable=False,
    )

    session: Mapped[SoutenanceSession] = relationship(
        "SoutenanceSession",
        back_populates="questions",
    )
    answer: Mapped[SoutenanceAnswer | None] = relationship(
        "SoutenanceAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class SoutenanceAnswer(Base):
    __tablename__ = "soutenance_answers"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            name="uq_soutenance_answers_question_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("soutenance_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    total_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[str] = mapped_column(Text, nullable=False)
    missing_concepts: Mapped[str] = mapped_column(Text, nullable=False)
    improved_answer: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )

    question: Mapped[SoutenanceQuestion] = relationship(
        "SoutenanceQuestion",
        back_populates="answer",
    )
    rubric_scores: Mapped[list[SoutenanceRubricScore]] = relationship(
        "SoutenanceRubricScore",
        back_populates="answer",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SoutenanceRubricScore.criterion",
    )


class SoutenanceRubricScore(Base):
    __tablename__ = "soutenance_rubric_scores"
    __table_args__ = (
        UniqueConstraint(
            "answer_id",
            "criterion",
            name="uq_soutenance_rubric_scores_answer_criterion",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    answer_id: Mapped[int] = mapped_column(
        ForeignKey("soutenance_answers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    criterion: Mapped[str] = mapped_column(String(80), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    answer: Mapped[SoutenanceAnswer] = relationship(
        "SoutenanceAnswer",
        back_populates="rubric_scores",
    )
