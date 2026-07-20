from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.documents import DocumentSort, DocumentStatus


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: int,
        title: str,
        original_filename: str,
        stored_filename: str,
        storage_key: str,
        mime_type: str,
        file_size: int,
        page_count: int,
        status: DocumentStatus = "uploaded",
    ) -> Document:
        document = Document(
            user_id=user_id,
            title=title,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size=file_size,
            page_count=page_count,
            status=status,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_owned(self, *, document_id: int, user_id: int) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_owned_by_ids(
        self,
        *,
        document_ids: list[int],
        user_id: int,
    ) -> list[Document]:
        if not document_ids:
            return []

        statement = (
            select(Document)
            .where(
                Document.user_id == user_id,
                Document.id.in_(document_ids),
            )
            .order_by(Document.created_at.desc(), Document.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_owned(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
        search: str | None,
        status: DocumentStatus | None,
        sort: DocumentSort,
    ) -> tuple[list[Document], int]:
        filters = [Document.user_id == user_id]

        if status is not None:
            filters.append(Document.status == status)

        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Document.title.ilike(pattern),
                    Document.original_filename.ilike(pattern),
                ),
            )

        count_statement = select(func.count()).select_from(Document).where(*filters)
        total = self.db.scalar(count_statement) or 0

        order_by = {
            "newest": Document.created_at.desc(),
            "oldest": Document.created_at.asc(),
            "title_asc": Document.title.asc(),
            "title_desc": Document.title.desc(),
        }[sort]
        statement = (
            select(Document)
            .where(*filters)
            .order_by(order_by, Document.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(self.db.scalars(statement).all()), total

    def count_owned(self, *, user_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.user_id == user_id,
            )
        )
        return self.db.scalar(statement) or 0

    def update_status(
        self,
        *,
        document: Document,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document:
        document.status = status
        document.error_message = error_message
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()
