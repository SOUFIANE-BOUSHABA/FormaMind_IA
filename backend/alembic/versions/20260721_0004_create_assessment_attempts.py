"""create assessment attempts

Revision ID: 20260721_0004
Revises: 20260720_0003
Create Date: 2026-07-21 00:04:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260721_0004"
down_revision: str | None = "20260720_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("level", sa.String(length=40), nullable=True),
        sa.Column("strong_topics", sa.JSON(), nullable=True),
        sa.Column("weak_topics", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('in_progress', 'evaluating', 'evaluated')",
            name="ck_assessment_attempts_status",
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["assessments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessment_attempts_assessment_id"),
        "assessment_attempts",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_attempts_created_at"),
        "assessment_attempts",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_attempts_id"),
        "assessment_attempts",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_attempts_started_at"),
        "assessment_attempts",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_attempts_status"),
        "assessment_attempts",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_attempts_user_id"),
        "assessment_attempts",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "student_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), nullable=True),
        sa.Column("text_answer", sa.Text(), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False),
        sa.Column("evaluation_status", sa.String(length=24), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("points_awarded", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("missing_concepts", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            (
                "evaluation_status IS NULL OR evaluation_status IN "
                "('correct', 'partial', 'incorrect', 'unanswered')"
            ),
            name="ck_student_answers_evaluation_status",
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["assessment_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["selected_option_id"],
            ["question_options.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_student_answers_attempt_question",
        ),
    )
    op.create_index(
        op.f("ix_student_answers_attempt_id"),
        "student_answers",
        ["attempt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_answers_id"),
        "student_answers",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_answers_question_id"),
        "student_answers",
        ["question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_student_answers_question_id"), table_name="student_answers")
    op.drop_index(op.f("ix_student_answers_id"), table_name="student_answers")
    op.drop_index(op.f("ix_student_answers_attempt_id"), table_name="student_answers")
    op.drop_table("student_answers")
    op.drop_index(
        op.f("ix_assessment_attempts_user_id"),
        table_name="assessment_attempts",
    )
    op.drop_index(
        op.f("ix_assessment_attempts_status"),
        table_name="assessment_attempts",
    )
    op.drop_index(
        op.f("ix_assessment_attempts_started_at"),
        table_name="assessment_attempts",
    )
    op.drop_index(op.f("ix_assessment_attempts_id"), table_name="assessment_attempts")
    op.drop_index(
        op.f("ix_assessment_attempts_created_at"),
        table_name="assessment_attempts",
    )
    op.drop_index(
        op.f("ix_assessment_attempts_assessment_id"),
        table_name="assessment_attempts",
    )
    op.drop_table("assessment_attempts")
