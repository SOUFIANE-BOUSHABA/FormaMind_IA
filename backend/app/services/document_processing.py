from __future__ import annotations

from app.models.document import Document
from app.models.user import User
from app.rag.embedding_service import EmbeddingService
from app.rag.pdf_extractor import (
    EmptyPdfTextError,
    PdfTextExtractionError,
    PdfTextExtractor,
)
from app.rag.text_chunker import TextChunker
from app.rag.vector_store import ChromaVectorStore, VectorStoreError
from app.repositories.document import DocumentRepository
from app.schemas.rag import ProcessDocumentResponse
from app.storage.documents import DocumentStorageService


class DocumentProcessingError(Exception):
    message = "Impossible d'analyser ce document."


class DocumentNotProcessableError(DocumentProcessingError):
    message = "Ce document ne peut pas être analysé dans son état actuel."


class NoUsableTextError(DocumentProcessingError):
    message = "Aucun texte exploitable n'a été trouvé dans ce PDF."


class DocumentProcessingService:
    allowed_statuses = {"uploaded", "failed", "ready"}

    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        storage_service: DocumentStorageService,
        pdf_extractor: PdfTextExtractor,
        text_chunker: TextChunker,
        embedding_service: EmbeddingService,
        vector_store: ChromaVectorStore,
    ) -> None:
        self.document_repository = document_repository
        self.storage_service = storage_service
        self.pdf_extractor = pdf_extractor
        self.text_chunker = text_chunker
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def process_document(
        self,
        *,
        user: User,
        document_id: int,
    ) -> ProcessDocumentResponse:
        document = self._get_processable_document(user=user, document_id=document_id)

        self.document_repository.update_status(
            document=document,
            status="processing",
            error_message=None,
        )

        try:
            self.vector_store.delete_document_chunks(
                user_id=user.id,
                document_id=document.id,
            )
            pdf_path = self.storage_service.path_for_key(document.storage_key)
            pages = self.pdf_extractor.extract_pages(
                pdf_path=pdf_path,
                document_id=document.id,
                user_id=user.id,
                document_title=document.title,
            )
            chunks = self.text_chunker.chunk_pages(pages)
            embeddings = self.embedding_service.embed_texts(
                [chunk.text for chunk in chunks]
            )
            self.vector_store.upsert_chunks(chunks=chunks, embeddings=embeddings)
        except EmptyPdfTextError as exc:
            self._mark_failed(document=document, message=NoUsableTextError.message)
            raise NoUsableTextError from exc
        except (PdfTextExtractionError, VectorStoreError) as exc:
            self._mark_failed(
                document=document,
                message=DocumentProcessingError.message,
            )
            raise DocumentProcessingError from exc
        except Exception as exc:
            self._mark_failed(
                document=document,
                message=DocumentProcessingError.message,
            )
            raise DocumentProcessingError from exc

        ready_document = self.document_repository.update_status(
            document=document,
            status="ready",
            error_message=None,
        )

        return ProcessDocumentResponse(
            document_id=ready_document.id,
            status=ready_document.status,
            page_count=ready_document.page_count,
            chunk_count=len(chunks),
            message="Document analysé avec succès.",
        )

    def _get_processable_document(self, *, user: User, document_id: int) -> Document:
        document = self.document_repository.get_owned(
            document_id=document_id,
            user_id=user.id,
        )
        if document is None:
            raise DocumentProcessingError

        if document.status not in self.allowed_statuses:
            raise DocumentNotProcessableError

        return document

    def _mark_failed(self, *, document: Document, message: str) -> None:
        self.document_repository.update_status(
            document=document,
            status="failed",
            error_message=message,
        )
