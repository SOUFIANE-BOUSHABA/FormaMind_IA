"""create learning plans

Revision ID: 20260723_0005
Revises: 20260721_0004
Create Date: 2026-07-23 00:05:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260723_0005"
down_revision: str | None = "20260721_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("intensity", sa.String(length=24), nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_end_date", sa.Date(), nullable=False),
        sa.Column("progress_percentage", sa.Integer(), nullable=False),
        sa.Column("generated_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'completed')",
            name="ck_learning_plans_status",
        ),
        sa.CheckConstraint(
            "intensity IN ('light', 'balanced', 'intensive')",
            name="ck_learning_plans_intensity",
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["assessment_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_plans_attempt_id"),
        "learning_plans",
        ["attempt_id"],
    )
    op.create_index(
        op.f("ix_learning_plans_created_at"),
        "learning_plans",
        ["created_at"],
    )
    op.create_index(op.f("ix_learning_plans_id"), "learning_plans", ["id"])
    op.create_index(op.f("ix_learning_plans_status"), "learning_plans", ["status"])
    op.create_index(op.f("ix_learning_plans_user_id"), "learning_plans", ["user_id"])

    op.create_table(
        "learning_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("topic", sa.String(length=180), nullable=False),
        sa.Column("priority", sa.String(length=24), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "priority IN ('high', 'medium', 'low')",
            name="ck_learning_modules_priority",
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["learning_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_modules_id"), "learning_modules", ["id"])
    op.create_index(
        op.f("ix_learning_modules_plan_id"),
        "learning_modules",
        ["plan_id"],
    )

    op.create_table(
        "learning_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('review', 'practice', 'quiz', 'reflection')",
            name="ck_learning_activities_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed')",
            name="ck_learning_activities_status",
        ),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["learning_modules.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_activities_id"), "learning_activities", ["id"])
    op.create_index(
        op.f("ix_learning_activities_module_id"),
        "learning_activities",
        ["module_id"],
    )
    op.create_index(
        op.f("ix_learning_activities_scheduled_date"),
        "learning_activities",
        ["scheduled_date"],
    )
    op.create_index(
        op.f("ix_learning_activities_status"),
        "learning_activities",
        ["status"],
    )

    op.create_table(
        "learning_activity_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["learning_activities.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_activity_sources_activity_id"),
        "learning_activity_sources",
        ["activity_id"],
    )
    op.create_index(
        op.f("ix_learning_activity_sources_document_id"),
        "learning_activity_sources",
        ["document_id"],
    )
    op.create_index(
        op.f("ix_learning_activity_sources_id"),
        "learning_activity_sources",
        ["id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_activity_sources_id"), "learning_activity_sources")
    op.drop_index(
        op.f("ix_learning_activity_sources_document_id"),
        "learning_activity_sources",
    )
    op.drop_index(
        op.f("ix_learning_activity_sources_activity_id"),
        "learning_activity_sources",
    )
    op.drop_table("learning_activity_sources")
    op.drop_index(op.f("ix_learning_activities_status"), "learning_activities")
    op.drop_index(
        op.f("ix_learning_activities_scheduled_date"),
        "learning_activities",
    )
    op.drop_index(op.f("ix_learning_activities_module_id"), "learning_activities")
    op.drop_index(op.f("ix_learning_activities_id"), "learning_activities")
    op.drop_table("learning_activities")
    op.drop_index(op.f("ix_learning_modules_plan_id"), "learning_modules")
    op.drop_index(op.f("ix_learning_modules_id"), "learning_modules")
    op.drop_table("learning_modules")
    op.drop_index(op.f("ix_learning_plans_user_id"), "learning_plans")
    op.drop_index(op.f("ix_learning_plans_status"), "learning_plans")
    op.drop_index(op.f("ix_learning_plans_id"), "learning_plans")
    op.drop_index(op.f("ix_learning_plans_created_at"), "learning_plans")
    op.drop_index(op.f("ix_learning_plans_attempt_id"), "learning_plans")
    op.drop_table("learning_plans")
