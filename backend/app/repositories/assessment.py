from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.assessment import (
    Assessment,
    AssessmentDocument,
    Question,
)
from app.models.document import Document
from app.schemas.assessment import AssessmentSort


class AssessmentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, assessment: Assessment) -> Assessment:
        self._db.add(assessment)
        self._db.flush()
        return assessment

    def get_by_id_for_user(
        self,
        *,
        assessment_id: int,
        user_id: int,
    ) -> Assessment | None:
        statement = (
            select(Assessment)
            .where(Assessment.id == assessment_id, Assessment.user_id == user_id)
            .options(
                selectinload(Assessment.documents).joinedload(
                    AssessmentDocument.document
                ),
                selectinload(Assessment.questions).options(
                    joinedload(Question.options),
                    joinedload(Question.source_document),
                ),
            )
        )
        return self._db.scalars(statement).first()

    def list_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
        sort: AssessmentSort,
    ) -> tuple[list[Assessment], int]:
        base_statement = select(Assessment).where(Assessment.user_id == user_id)
        total = self._count(base_statement)

        order_by = Assessment.created_at.desc()
        if sort == "oldest":
            order_by = Assessment.created_at.asc()
       

        statement = (
            base_statement.order_by(order_by)
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Assessment.documents).joinedload(
                    AssessmentDocument.document
                ),
            )
        )

        return list(self._db.scalars(statement).all()), total

    def commit(self) -> None:
        self._db.commit()

    def refresh(self, assessment: Assessment) -> None:
        self._db.refresh(assessment)

    def _count(self, statement: Select[tuple[Assessment]]) -> int:
        count_statement = select(func.count()).select_from(statement.subquery())
        return self._db.scalar(count_statement) or 0


def get_ready_documents_for_user(
    *,
    db: Session,
    user_id: int,
    document_ids: list[int],
) -> list[Document]:
    statement = (
        select(Document)
        .where(
            Document.user_id == user_id,
            Document.id.in_(document_ids),
            Document.status == "ready",
        )
        .order_by(Document.id.asc())
    )
    return list(db.scalars(statement).all())