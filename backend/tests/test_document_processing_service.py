from __future__ import annotations

from pathlib import Path

import pytest

from app.models.document import Document
from app.models.user import User
from app.rag.pdf_extractor import EmptyPdfTextError, PdfTextExtractionError
from app.schemas.rag import ExtractedPage, TextChunk
from app.services.document_processing import (
    DocumentNotProcessableError,
    DocumentProcessingError,
    DocumentProcessingService,
    NoUsableTextError,
)


def make_user() -> User:
    return User(
        id=5,
        email="learner@example.com",
        full_name="Learner",
        hashed_password="hash",
    )


def make_document(status: str = "uploaded") -> Document:
    return Document(
        id=10,
        user_id=5,
        title="Cours RAG",
        original_filename="cours-rag.pdf",
        stored_filename="uuid.pdf",
        storage_key="5/uuid.pdf",
        mime_type="application/pdf",
        file_size=100,
        page_count=2,
        status=status,
    )


class FakeDocumentRepository:
    def __init__(self, document: Document | None) -> None:
        self.document = document
        self.status_updates: list[tuple[str, str | None]] = []

    def get_owned(self, *, document_id: int, user_id: int) -> Document | None:
        if (
            self.document is not None
            and self.document.id == document_id
            and self.document.user_id == user_id
        ):
            return self.document
        return None

    def update_status(
        self,
        *,
        document: Document,
        status: str,
        error_message: str | None = None,
    ) -> Document:
        document.status = status
        document.error_message = error_message
        self.status_updates.append((status, error_message))
        return document


class FakeStorageService:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def path_for_key(self, storage_key: str) -> Path:
        self.paths.append(storage_key)
        return Path("fake.pdf")


class FakePdfExtractor:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def extract_pages(
        self,
        *,
        pdf_path: Path,
        document_id: int,
        user_id: int,
        document_title: str,
    ) -> list[ExtractedPage]:
        if self.error is not None:
            raise self.error
        return [
            ExtractedPage(
                document_id=document_id,
                user_id=user_id,
                document_title=document_title,
                page_number=1,
                text="Le RAG combine recherche et generation.",
            )
        ]


class FakeTextChunker:
    def chunk_pages(self, pages: list[ExtractedPage]) -> list[TextChunk]:
        page = pages[0]
        return [
            TextChunk(
                document_id=page.document_id,
                user_id=page.user_id,
                document_title=page.document_title,
                page_number=page.page_number,
                chunk_index=0,
                text=page.text,
            )
        ]


class FakeEmbeddingService:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _text in texts]


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted: list[tuple[int, int]] = []
        self.upserts: list[tuple[list[TextChunk], list[list[float]]]] = []

    def delete_document_chunks(self, *, user_id: int, document_id: int) -> None:
        self.deleted.append((user_id, document_id))

    def upsert_chunks(
        self,
        *,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:
        self.upserts.append((chunks, embeddings))


def make_service(
    *,
    repository: FakeDocumentRepository,
    extractor: FakePdfExtractor | None = None,
    vector_store: FakeVectorStore | None = None,
) -> tuple[DocumentProcessingService, FakeVectorStore]:
    store = vector_store or FakeVectorStore()
    service = DocumentProcessingService(
        document_repository=repository,
        storage_service=FakeStorageService(),
        pdf_extractor=extractor or FakePdfExtractor(),
        text_chunker=FakeTextChunker(),
        embedding_service=FakeEmbeddingService(),
        vector_store=store,
    )
    return service, store


def test_document_processing_marks_processing_then_ready() -> None:
    repository = FakeDocumentRepository(document=make_document())
    service, vector_store = make_service(repository=repository)

    response = service.process_document(user=make_user(), document_id=10)

    assert repository.status_updates == [("processing", None), ("ready", None)]
    assert vector_store.deleted == [(5, 10)]
    assert len(vector_store.upserts) == 1
    assert response.status == "ready"
    assert response.chunk_count == 1


def test_document_processing_rejects_non_processable_status() -> None:
    repository = FakeDocumentRepository(document=make_document(status="processing"))
    service, _vector_store = make_service(repository=repository)

    with pytest.raises(DocumentNotProcessableError):
        service.process_document(user=make_user(), document_id=10)

    assert repository.status_updates == []


def test_document_processing_marks_failed_when_pdf_has_no_text() -> None:
    repository = FakeDocumentRepository(document=make_document())
    service, _vector_store = make_service(
        repository=repository,
        extractor=FakePdfExtractor(error=EmptyPdfTextError()),
    )

    with pytest.raises(NoUsableTextError):
        service.process_document(user=make_user(), document_id=10)

    assert repository.status_updates == [
        ("processing", None),
        ("failed", NoUsableTextError.message),
    ]


def test_document_processing_marks_failed_on_extraction_error() -> None:
    repository = FakeDocumentRepository(document=make_document())
    service, _vector_store = make_service(
        repository=repository,
        extractor=FakePdfExtractor(error=PdfTextExtractionError()),
    )

    with pytest.raises(DocumentProcessingError):
        service.process_document(user=make_user(), document_id=10)

    assert repository.status_updates == [
        ("processing", None),
        ("failed", DocumentProcessingError.message),
    ]
