from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    Question,
    StudentAnswer,
)
from app.models.learning_plan import (
    LearningActivity,
    LearningActivitySource,
    LearningModule,
    LearningPlan,
)


class LearningPlanRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_attempt_for_generation(
        self,
        *,
        attempt_id: int,
        user_id: int,
    ) -> AssessmentAttempt | None:
        statement = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.user_id == user_id,
            )
            .options(
                joinedload(AssessmentAttempt.assessment).options(
                    selectinload(Assessment.questions).options(
                        joinedload(Question.source_document),
                    ),
                    selectinload(Assessment.documents),
                ),
                selectinload(AssessmentAttempt.answers).options(
                    joinedload(StudentAnswer.question),
                    joinedload(StudentAnswer.selected_option),
                ),
            )
        )
        return self._db.scalars(statement).first()

    def add(self, plan: LearningPlan) -> LearningPlan:
        self._db.add(plan)
        self._db.flush()
        return plan

    def get_for_user(self, *, plan_id: int, user_id: int) -> LearningPlan | None:
        statement = (
            select(LearningPlan)
            .where(LearningPlan.id == plan_id, LearningPlan.user_id == user_id)
            .options(
                joinedload(LearningPlan.attempt).joinedload(
                    AssessmentAttempt.assessment,
                ),
                selectinload(LearningPlan.modules)
                .selectinload(LearningModule.activities)
                .selectinload(LearningActivity.sources)
                .joinedload(LearningActivitySource.document),
            )
        )
        return self._db.scalars(statement).unique().first()

    def list_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> tuple[list[LearningPlan], int]:
        base_statement = select(LearningPlan).where(LearningPlan.user_id == user_id)
        if status is not None:
            base_statement = base_statement.where(LearningPlan.status == status)

        total = self._count(base_statement)
        statement = (
            base_statement.order_by(LearningPlan.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(
                joinedload(LearningPlan.attempt).joinedload(
                    AssessmentAttempt.assessment,
                ),
                selectinload(LearningPlan.modules).selectinload(
                    LearningModule.activities,
                ),
            )
        )
        return list(self._db.scalars(statement).unique().all()), total

    def get_active_for_attempt(
        self,
        *,
        attempt_id: int,
        user_id: int,
    ) -> LearningPlan | None:
        statement = select(LearningPlan).where(
            LearningPlan.attempt_id == attempt_id,
            LearningPlan.user_id == user_id,
            LearningPlan.status == "active",
        )
        return self._db.scalars(statement).first()

    def latest_next_activity(
        self,
        *,
        user_id: int,
    ) -> tuple[LearningPlan, LearningActivity] | None:
        statement = (
            select(LearningPlan, LearningActivity)
            .join(LearningModule, LearningModule.plan_id == LearningPlan.id)
            .join(LearningActivity, LearningActivity.module_id == LearningModule.id)
            .where(
                LearningPlan.user_id == user_id,
                LearningPlan.status == "active",
                LearningActivity.status != "completed",
            )
            .order_by(
                LearningActivity.scheduled_date.asc(),
                LearningModule.order_index.asc(),
                LearningActivity.order_index.asc(),
            )
            .limit(1)
        )
        return self._db.execute(statement).first()

    def delete(self, plan: LearningPlan) -> None:
        self._db.delete(plan)

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def flush(self) -> None:
        self._db.flush()

    def refresh(self, plan: LearningPlan) -> None:
        self._db.refresh(plan)

    def _count(self, statement: Select[tuple[LearningPlan]]) -> int:
        count_statement = select(func.count()).select_from(statement.subquery())
        return self._db.scalar(count_statement) or 0
