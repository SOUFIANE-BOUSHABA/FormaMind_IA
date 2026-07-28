"""create soutenance sessions

Revision ID: 20260726_0006
Revises: 20260723_0005
Create Date: 2026-07-26 00:06:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260726_0006"
down_revision: str | None = "20260723_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "soutenance_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("introduction", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False),
        sa.Column("difficulty", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("current_question_index", sa.Integer(), nullable=False),
        sa.Column("final_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("readiness_level", sa.String(length=60), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("weaknesses", sa.Text(), nullable=True),
        sa.Column("missing_concepts", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "mode IN ('training', 'jury')",
            name="ck_soutenance_sessions_mode",
        ),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'adaptive')",
            name="ck_soutenance_sessions_difficulty",
        ),
        sa.CheckConstraint(
            "status IN ('in_progress', 'completed')",
            name="ck_soutenance_sessions_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_soutenance_sessions_created_at"),
        "soutenance_sessions",
        ["created_at"],
    )
    op.create_index(op.f("ix_soutenance_sessions_id"), "soutenance_sessions", ["id"])
    op.create_index(
        op.f("ix_soutenance_sessions_status"),
        "soutenance_sessions",
        ["status"],
    )
    op.create_index(
        op.f("ix_soutenance_sessions_user_id"),
        "soutenance_sessions",
        ["user_id"],
    )

    op.create_table(
        "soutenance_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("local_id", sa.String(length=60), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("difficulty", sa.String(length=24), nullable=False),
        sa.Column("expected_concepts", sa.Text(), nullable=False),
        sa.Column("evaluation_focus", sa.Text(), nullable=False),
        sa.Column("follow_up_hint", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("answer_status", sa.String(length=24), nullable=False),
        sa.CheckConstraint(
            (
                "category IN ('technical', 'architecture', 'ai_concepts', "
                "'security', 'project_choices', 'limitations', 'testing', "
                "'deployment', 'jury_challenge')"
            ),
            name="ck_soutenance_questions_category",
        ),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'adaptive')",
            name="ck_soutenance_questions_difficulty",
        ),
        sa.CheckConstraint(
            "answer_status IN ('waiting', 'answered')",
            name="ck_soutenance_questions_answer_status",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["soutenance_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "local_id",
            name="uq_soutenance_questions_session_local_id",
        ),
    )
    op.create_index(
        op.f("ix_soutenance_questions_category"),
        "soutenance_questions",
        ["category"],
    )
    op.create_index(op.f("ix_soutenance_questions_id"), "soutenance_questions", ["id"])
    op.create_index(
        op.f("ix_soutenance_questions_session_id"),
        "soutenance_questions",
        ["session_id"],
    )
    op.create_index(
        op.f("ix_soutenance_questions_answer_status"),
        "soutenance_questions",
        ["answer_status"],
    )

    op.create_table(
        "soutenance_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("total_score", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=False),
        sa.Column("missing_concepts", sa.Text(), nullable=False),
        sa.Column("improved_answer", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["soutenance_questions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "question_id",
            name="uq_soutenance_answers_question_id",
        ),
    )
    op.create_index(
        op.f("ix_soutenance_answers_created_at"),
        "soutenance_answers",
        ["created_at"],
    )
    op.create_index(op.f("ix_soutenance_answers_id"), "soutenance_answers", ["id"])
    op.create_index(
        op.f("ix_soutenance_answers_question_id"),
        "soutenance_answers",
        ["question_id"],
    )

    op.create_table(
        "soutenance_rubric_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("criterion", sa.String(length=80), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["soutenance_answers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "answer_id",
            "criterion",
            name="uq_soutenance_rubric_scores_answer_criterion",
        ),
    )
    op.create_index(
        op.f("ix_soutenance_rubric_scores_answer_id"),
        "soutenance_rubric_scores",
        ["answer_id"],
    )
    op.create_index(
        op.f("ix_soutenance_rubric_scores_id"),
        "soutenance_rubric_scores",
        ["id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_soutenance_rubric_scores_id"),
        table_name="soutenance_rubric_scores",
    )
    op.drop_index(
        op.f("ix_soutenance_rubric_scores_answer_id"),
        table_name="soutenance_rubric_scores",
    )
    op.drop_table("soutenance_rubric_scores")
    op.drop_index(
        op.f("ix_soutenance_answers_question_id"),
        table_name="soutenance_answers",
    )
    op.drop_index(op.f("ix_soutenance_answers_id"), table_name="soutenance_answers")
    op.drop_index(
        op.f("ix_soutenance_answers_created_at"),
        table_name="soutenance_answers",
    )
    op.drop_table("soutenance_answers")
    op.drop_index(
        op.f("ix_soutenance_questions_answer_status"),
        table_name="soutenance_questions",
    )
    op.drop_index(
        op.f("ix_soutenance_questions_session_id"),
        table_name="soutenance_questions",
    )
    op.drop_index(
        op.f("ix_soutenance_questions_id"),
        table_name="soutenance_questions",
    )
    op.drop_index(
        op.f("ix_soutenance_questions_category"),
        table_name="soutenance_questions",
    )
    op.drop_table("soutenance_questions")
    op.drop_index(
        op.f("ix_soutenance_sessions_user_id"),
        table_name="soutenance_sessions",
    )
    op.drop_index(
        op.f("ix_soutenance_sessions_status"),
        table_name="soutenance_sessions",
    )
    op.drop_index(op.f("ix_soutenance_sessions_id"), table_name="soutenance_sessions")
    op.drop_index(
        op.f("ix_soutenance_sessions_created_at"),
        table_name="soutenance_sessions",
    )
    op.drop_table("soutenance_sessions")
