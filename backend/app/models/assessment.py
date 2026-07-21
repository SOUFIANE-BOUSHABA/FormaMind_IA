from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User

AssessmentDifficulty = Literal["beginner", "intermediate", "advanced", "adaptive"]
AssessmentStatus = Literal["generated", "in_progress", "completed"]
QuestionType = Literal[
    "multiple_choice",
    "true_false",
    "short_answer",
    "explanation",
]


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'adaptive')",
            name="ck_assessments_difficulty",
        ),
        CheckConstraint(
            "status IN ('generated', 'in_progress', 'completed')",
            name="ck_assessments_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24),
        default="generated",
        index=True,
        nullable=False,
    )
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
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

    user: Mapped[User] = relationship("User", back_populates="assessments")
    documents: Mapped[list[AssessmentDocument]] = relationship(
        "AssessmentDocument",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    questions: Mapped[list[Question]] = relationship(
        "Question",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Question.order_index",
    )


class AssessmentDocument(Base):
    __tablename__ = "assessment_documents"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "document_id",
            name="uq_assessment_documents_assessment_document",
        ),
    )

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )

    assessment: Mapped[Assessment] = relationship(
        "Assessment",
        back_populates="documents",
    )
    document: Mapped[Document] = relationship("Document")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "type IN ('multiple_choice', 'true_false', 'short_answer', 'explanation')",
            name="ck_questions_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    assessment: Mapped[Assessment] = relationship(
        "Assessment",
        back_populates="questions",
    )
    options: Mapped[list[QuestionOption]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuestionOption.order_index",
    )
    source_document: Mapped[Document] = relationship("Document")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped[Question] = relationship(
        "Question",
        back_populates="options",
    )