"""create assessments tables

Revision ID: 20260720_0003
Revises: 20260718_0002
Create Date: 2026-07-20 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260720_0003"
down_revision: str | None = "20260718_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("difficulty", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'adaptive')",
            name="ck_assessments_difficulty",
        ),
        sa.CheckConstraint(
            "status IN ('generated', 'in_progress', 'completed')",
            name="ck_assessments_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assessments_created_at"), "assessments", ["created_at"])
    op.create_index(op.f("ix_assessments_difficulty"), "assessments", ["difficulty"])
    op.create_index(op.f("ix_assessments_id"), "assessments", ["id"])
    op.create_index(op.f("ix_assessments_status"), "assessments", ["status"])
    op.create_index(op.f("ix_assessments_user_id"), "assessments", ["user_id"])

    op.create_table(
        "assessment_documents",
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["assessments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("assessment_id", "document_id"),
        sa.UniqueConstraint(
            "assessment_id",
            "document_id",
            name="uq_assessment_documents_assessment_document",
        ),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("source_page_number", sa.Integer(), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "type IN ('multiple_choice', 'true_false', 'short_answer', 'explanation')",
            name="ck_questions_type",
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["assessments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["documents.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_assessment_id"), "questions", ["assessment_id"])
    op.create_index(op.f("ix_questions_id"), "questions", ["id"])

    op.create_table(
        "question_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_options_id"), "question_options", ["id"])
    op.create_index(
        op.f("ix_question_options_question_id"),
        "question_options",
        ["question_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_question_options_question_id"),
        table_name="question_options",
    )
    op.drop_index(op.f("ix_question_options_id"), table_name="question_options")
    op.drop_table("question_options")

    op.drop_index(op.f("ix_questions_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_assessment_id"), table_name="questions")
    op.drop_table("questions")

    op.drop_table("assessment_documents")

    op.drop_index(op.f("ix_assessments_user_id"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_status"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_id"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_difficulty"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_created_at"), table_name="assessments")
    op.drop_table("assessments")