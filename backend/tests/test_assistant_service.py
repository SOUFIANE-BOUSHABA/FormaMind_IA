from __future__ import annotations

import pytest

from app.models.document import Document
from app.models.user import User
from app.schemas.assistant import (
    AskQuestionRequest,
    KnowledgeAnswer,
    SourceCitation,
)
from app.services.assistant import (
    AssistantConfigurationError,
    AssistantProviderError,
    AssistantService,
    SelectedDocumentsNotFoundError,
    SelectedDocumentsNotReadyError,
)
from app.services.llm import LlmConfigurationError, LlmProviderError


def make_user() -> User:
    return User(
        id=5,
        email="learner@example.com",
        full_name="Learner",
        hashed_password="hash",
    )


def make_document(document_id: int, status: str = "ready") -> Document:
    return Document(
        id=document_id,
        user_id=5,
        title=f"Document {document_id}",
        original_filename=f"document-{document_id}.pdf",
        stored_filename=f"{document_id}.pdf",
        storage_key=f"5/{document_id}.pdf",
        mime_type="application/pdf",
        file_size=100,
        page_count=2,
        status=status,
    )


class FakeDocumentRepository:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        self.calls: list[tuple[list[int], int]] = []

    def list_owned_by_ids(
        self,
        *,
        document_ids: list[int],
        user_id: int,
    ) -> list[Document]:
        self.calls.append((document_ids, user_id))
        return [
            document
            for document in self.documents
            if document.id in document_ids and document.user_id == user_id
        ]


class FakeKnowledgeAgent:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[int, list[int], str]] = []

    def answer(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> KnowledgeAnswer:
        self.calls.append((user_id, document_ids, question))
        if self.error is not None:
            raise self.error
        return KnowledgeAnswer(
            answer="Reponse sourcee.",
            has_sufficient_context=True,
            sources=[
                SourceCitation(
                    document_id=document_ids[0],
                    document_title="Document 10",
                    page_number=1,
                    excerpt="Extrait source.",
                )
            ],
        )


def test_assistant_service_requires_owned_documents() -> None:
    repository = FakeDocumentRepository(documents=[make_document(10)])
    service = AssistantService(
        document_repository=repository,
        knowledge_agent=FakeKnowledgeAgent(),
    )

    with pytest.raises(SelectedDocumentsNotFoundError):
        service.ask_question(
            user=make_user(),
            request=AskQuestionRequest(document_ids=[10, 11], question="Question ?"),
        )


def test_assistant_service_requires_ready_documents() -> None:
    repository = FakeDocumentRepository(documents=[make_document(10, "uploaded")])
    service = AssistantService(
        document_repository=repository,
        knowledge_agent=FakeKnowledgeAgent(),
    )

    with pytest.raises(SelectedDocumentsNotReadyError):
        service.ask_question(
            user=make_user(),
            request=AskQuestionRequest(document_ids=[10], question="Question ?"),
        )


def test_assistant_service_deduplicates_documents_and_calls_agent() -> None:
    repository = FakeDocumentRepository(
        documents=[make_document(10), make_document(11)]
    )
    agent = FakeKnowledgeAgent()
    service = AssistantService(document_repository=repository, knowledge_agent=agent)

    response = service.ask_question(
        user=make_user(),
        request=AskQuestionRequest(document_ids=[10, 10, 11], question="Question ?"),
    )

    assert repository.calls == [([10, 11], 5)]
    assert agent.calls == [(5, [10, 11], "Question ?")]
    assert response.has_sufficient_context is True
    assert response.sources[0].document_id == 10


def test_assistant_service_maps_llm_configuration_error() -> None:
    repository = FakeDocumentRepository(documents=[make_document(10)])
    service = AssistantService(
        document_repository=repository,
        knowledge_agent=FakeKnowledgeAgent(error=LlmConfigurationError()),
    )

    with pytest.raises(AssistantConfigurationError):
        service.ask_question(
            user=make_user(),
            request=AskQuestionRequest(document_ids=[10], question="Question ?"),
        )


def test_assistant_service_maps_llm_provider_error() -> None:
    repository = FakeDocumentRepository(documents=[make_document(10)])
    service = AssistantService(
        document_repository=repository,
        knowledge_agent=FakeKnowledgeAgent(error=LlmProviderError()),
    )

    with pytest.raises(AssistantProviderError):
        service.ask_question(
            user=make_user(),
            request=AskQuestionRequest(document_ids=[10], question="Question ?"),
        )
