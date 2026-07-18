from __future__ import annotations

from math import ceil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.models.document import Document
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.schemas.documents import DocumentListResponse, DocumentSort, DocumentStatus
from app.storage.documents import DocumentStorageService


class DocumentNotFoundError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        storage: DocumentStorageService,
    ) -> None:
        self.repository = repository
        self.storage = storage

    def upload_document(
        self,
        *,
        user: User,
        file: UploadFile,
        title: str | None,
    ) -> Document:
        stored_document = self.storage.store_pdf(file=file, user_id=user.id)
        cleaned_title = self._resolve_title(title=title, filename=file.filename)

        try:
            return self.repository.create(
                user_id=user.id,
                title=cleaned_title,
                original_filename=Path(file.filename or "document.pdf").name,
                stored_filename=stored_document.stored_filename,
                storage_key=stored_document.storage_key,
                mime_type=stored_document.mime_type,
                file_size=stored_document.file_size,
                page_count=stored_document.page_count,
            )
        except SQLAlchemyError:
            self.storage.delete_by_key(stored_document.storage_key)
            raise

    def list_documents(
        self,
        *,
        user: User,
        page: int,
        page_size: int,
        search: str | None,
        status: DocumentStatus | None,
        sort: DocumentSort,
    ) -> DocumentListResponse:
        documents, total = self.repository.list_owned(
            user_id=user.id,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            sort=sort,
        )
        total_pages = ceil(total / page_size) if total else 0
        return DocumentListResponse(
            items=documents,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    def get_document(self, *, user: User, document_id: int) -> Document:
        document = self.repository.get_owned(document_id=document_id, user_id=user.id)
        if document is None:
            raise DocumentNotFoundError
        return document

    def delete_document(self, *, user: User, document_id: int) -> None:
        document = self.get_document(user=user, document_id=document_id)
        storage_key = document.storage_key
        self.repository.delete(document)
        self.storage.delete_by_key(storage_key)

    def count_documents(self, *, user: User) -> int:
        return self.repository.count_owned(user_id=user.id)

    @staticmethod
    def _resolve_title(*, title: str | None, filename: str | None) -> str:
        if title and title.strip():
            return title.strip()[:180]

        original_filename = Path(filename or "document.pdf").name
        stem = Path(original_filename).stem.strip()
        return (stem or "Document PDF")[:180]
