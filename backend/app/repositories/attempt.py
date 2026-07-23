from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    Question,
    StudentAnswer,
)


class AttemptRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_assessment_for_user(
        self,
        *,
        assessment_id: int,
        user_id: int,
    ) -> Assessment | None:
        statement = (
            select(Assessment)
            .where(Assessment.id == assessment_id, Assessment.user_id == user_id)
            .options(
                selectinload(Assessment.questions).options(
                    joinedload(Question.options),
                    joinedload(Question.source_document),
                ),
            )
        )
        return self._db.scalars(statement).first()

    def get_in_progress_attempt(
        self,
        *,
        assessment_id: int,
        user_id: int,
    ) -> AssessmentAttempt | None:
        statement = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.assessment_id == assessment_id,
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.status == "in_progress",
            )
            .order_by(AssessmentAttempt.created_at.desc())
            .options(
                joinedload(AssessmentAttempt.assessment),
                selectinload(AssessmentAttempt.answers),
            )
        )
        return self._db.scalars(statement).first()

    def get_attempt_for_user(
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
                        joinedload(Question.options),
                        joinedload(Question.source_document),
                    ),
                ),
                selectinload(AssessmentAttempt.answers).options(
                    joinedload(StudentAnswer.question),
                    joinedload(StudentAnswer.selected_option),
                ),
            )
        )
        return self._db.scalars(statement).first()

    def list_for_assessment(
        self,
        *,
        assessment_id: int,
        user_id: int,
        limit: int,
        offset: int,
        status: str | None,
    ) -> tuple[list[AssessmentAttempt], int]:
        base_statement = select(AssessmentAttempt).where(
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.user_id == user_id,
        )
        if status is not None:
            base_statement = base_statement.where(AssessmentAttempt.status == status)

        total = self._count(base_statement)
        statement = (
            base_statement.order_by(AssessmentAttempt.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(
                joinedload(AssessmentAttempt.assessment),
                selectinload(AssessmentAttempt.answers),
            )
        )
        return list(self._db.scalars(statement).all()), total

    def get_answer(
        self,
        *,
        attempt_id: int,
        question_id: int,
    ) -> StudentAnswer | None:
        statement = select(StudentAnswer).where(
            StudentAnswer.attempt_id == attempt_id,
            StudentAnswer.question_id == question_id,
        )
        return self._db.scalars(statement).first()

    def add_attempt(self, attempt: AssessmentAttempt) -> AssessmentAttempt:
        self._db.add(attempt)
        self._db.flush()
        return attempt

    def add_answer(self, answer: StudentAnswer) -> StudentAnswer:
        self._db.add(answer)
        self._db.flush()
        return answer

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def flush(self) -> None:
        self._db.flush()

    def _count(self, statement: Select[tuple[AssessmentAttempt]]) -> int:
        count_statement = select(func.count()).select_from(statement.subquery())
        return self._db.scalar(count_statement) or 0
