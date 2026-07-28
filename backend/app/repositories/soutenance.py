from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.assessment import Assessment, AssessmentAttempt, Question, StudentAnswer
from app.models.learning_plan import LearningModule, LearningPlan
from app.models.soutenance import (
    SoutenanceAnswer,
    SoutenanceQuestion,
    SoutenanceSession,
)


class SoutenanceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, session: SoutenanceSession) -> SoutenanceSession:
        self._db.add(session)
        self._db.flush()
        return session

    def add_answer(self, answer: SoutenanceAnswer) -> SoutenanceAnswer:
        self._db.add(answer)
        self._db.flush()
        return answer

    def get_for_user(
        self,
        *,
        session_id: int,
        user_id: int,
    ) -> SoutenanceSession | None:
        statement = (
            select(SoutenanceSession)
            .where(
                SoutenanceSession.id == session_id,
                SoutenanceSession.user_id == user_id,
            )
            .options(*self._session_options())
        )
        return self._db.scalars(statement).unique().first()

    def list_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
        status: str | None,
    ) -> tuple[list[SoutenanceSession], int]:
        base_statement = select(SoutenanceSession).where(
            SoutenanceSession.user_id == user_id
        )
        if status is not None:
            base_statement = base_statement.where(SoutenanceSession.status == status)

        total = self._count(base_statement)
        statement = (
            base_statement.order_by(SoutenanceSession.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(*self._session_options())
        )
        return list(self._db.scalars(statement).unique().all()), total

    def learner_attempts(
        self,
        *,
        user_id: int,
        limit: int = 5,
    ) -> list[AssessmentAttempt]:
        statement = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.status == "evaluated",
            )
            .order_by(AssessmentAttempt.evaluated_at.desc())
            .limit(limit)
            .options(
                joinedload(AssessmentAttempt.assessment).options(
                    selectinload(Assessment.questions).joinedload(
                        Question.source_document
                    )
                ),
                selectinload(AssessmentAttempt.answers).joinedload(
                    StudentAnswer.question
                ),
            )
        )
        return list(self._db.scalars(statement).unique().all())

    def learner_learning_plans(
        self,
        *,
        user_id: int,
        limit: int = 5,
    ) -> list[LearningPlan]:
        statement = (
            select(LearningPlan)
            .where(LearningPlan.user_id == user_id)
            .order_by(LearningPlan.created_at.desc())
            .limit(limit)
            .options(
                selectinload(LearningPlan.modules).selectinload(
                    LearningModule.activities
                )
            )
        )
        return list(self._db.scalars(statement).unique().all())

    def completed_sessions(
        self,
        *,
        user_id: int,
        limit: int = 5,
    ) -> list[SoutenanceSession]:
        statement = (
            select(SoutenanceSession)
            .where(
                SoutenanceSession.user_id == user_id,
                SoutenanceSession.status == "completed",
            )
            .order_by(SoutenanceSession.completed_at.desc())
            .limit(limit)
            .options(*self._session_options())
        )
        return list(self._db.scalars(statement).unique().all())

    def latest_in_progress(
        self,
        *,
        user_id: int,
    ) -> SoutenanceSession | None:
        statement = (
            select(SoutenanceSession)
            .where(
                SoutenanceSession.user_id == user_id,
                SoutenanceSession.status == "in_progress",
            )
            .order_by(SoutenanceSession.updated_at.desc())
            .options(*self._session_options())
            .limit(1)
        )
        return self._db.scalars(statement).unique().first()

    def delete(self, session: SoutenanceSession) -> None:
        self._db.delete(session)

    def flush(self) -> None:
        self._db.flush()

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def _session_options(self) -> tuple[object, ...]:
        return (
            selectinload(SoutenanceSession.questions)
            .selectinload(SoutenanceQuestion.answer)
            .selectinload(SoutenanceAnswer.rubric_scores),
        )

    def _count(self, statement: Select[tuple[SoutenanceSession]]) -> int:
        count_statement = select(func.count()).select_from(statement.subquery())
        return self._db.scalar(count_statement) or 0
