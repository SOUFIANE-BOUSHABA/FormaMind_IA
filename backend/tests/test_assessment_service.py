from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.models.document import Document
from app.models.user import User
from app.schemas.assessment import AssessmentDraft, GenerateAssessmentRequest
from app.schemas.rag import RetrievedChunk
from app.services.assessment import (
    AssessmentDocumentsNotFoundError,
    AssessmentGenerationInvalidOutputError,
    AssessmentService,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def make_settings() -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite:///./test.db",
        access_token_secret="access-secret",
        refresh_token_secret="refresh-secret",
        gemini_api_key="test-key",
        gemini_model="gemini-2.0-flash",
    )


def make_user() -> User:
    return User(
        email="learner@example.com",
        full_name="Learner",
        hashed_password="hash",
    )


def make_document(
    *,
    user: User,
    document_id: int = 10,
    status: str = "ready",
) -> Document:
    return Document(
        id=document_id,
        user=user,
        title=f"Document {document_id}",
        original_filename=f"document-{document_id}.pdf",
        stored_filename=f"{document_id}.pdf",
        storage_key=f"{user.id}/{document_id}.pdf",
        mime_type="application/pdf",
        file_size=100,
        page_count=2,
        status=status,
    )


def make_request() -> GenerateAssessmentRequest:
    return GenerateAssessmentRequest(
        document_ids=[10],
        topics=["RAG"],
        difficulty="intermediate",
        question_count=3,
        question_types=["multiple_choice"],
    )


def make_draft(source_ref: str = "SOURCE_1") -> AssessmentDraft:
    return AssessmentDraft(
        title="Evaluation RAG",
        difficulty="intermediate",
        questions=[
            {
                "type": "multiple_choice",
                "text": "Quel est le role principal du RAG ?",
                "options": [
                    {"text": "Chercher du contexte", "is_correct": True},
                    {"text": "Compresser des images", "is_correct": False},
                    {"text": "Compiler du code", "is_correct": False},
                    {"text": "Creer une base SQL", "is_correct": False},
                ],
                "correct_answer": "Chercher du contexte",
                "explanation": "Le RAG recupere un contexte avant generation.",
                "points": 1,
                "source_ref": source_ref,
            },
            {
                "type": "multiple_choice",
                "text": "Pourquoi citer une source ?",
                "options": [
                    {"text": "Pour tracer la reponse", "is_correct": True},
                    {"text": "Pour masquer le contexte", "is_correct": False},
                    {"text": "Pour ignorer le document", "is_correct": False},
                    {"text": "Pour supprimer la reponse", "is_correct": False},
                ],
                "correct_answer": "Pour tracer la reponse",
                "explanation": "La citation relie la question au document.",
                "points": 1,
                "source_ref": source_ref,
            },
            {
                "type": "multiple_choice",
                "text": "Que doit eviter l'agent ?",
                "options": [
                    {"text": "Inventer une information", "is_correct": True},
                    {"text": "Utiliser le contexte", "is_correct": False},
                    {"text": "Citer une page", "is_correct": False},
                    {"text": "Respecter le niveau", "is_correct": False},
                ],
                "correct_answer": "Inventer une information",
                "explanation": "L'agent doit rester fonde sur les documents.",
                "points": 1,
                "source_ref": source_ref,
            },
        ],
    )


class FakeAssessmentAgent:
    def __init__(self, draft: AssessmentDraft | None = None) -> None:
        self.draft = draft or make_draft()

    def generate_assessment(
        self,
        *,
        request: GenerateAssessmentRequest,
        context_tool: object,
    ) -> AssessmentDraft:
        context_tool._run(topic=request.topics[0], difficulty=request.difficulty)
        return self.draft


class FakeRetrieverTool:
    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                vector_id="document-10-page-1-chunk-0",
                user_id=user_id,
                document_id=document_ids[0],
                document_title="Document 10",
                page_number=1,
                chunk_index=0,
                text=f"Source pour {question}",
                score=0.93,
            )
        ]


def test_assessment_service_generates_and_persists_assessment(
    db_session: Session,
) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    db_session.add(make_document(user=user))
    db_session.commit()

    service = AssessmentService(
        db=db_session,
        settings=make_settings(),
        assessment_agent=FakeAssessmentAgent(),
        retriever_tool=FakeRetrieverTool(),
    )

    response = service.generate_assessment(
        current_user=user,
        request=make_request(),
    )

    assert response.title == "Evaluation RAG"
    assert response.question_count == 3
    assert response.documents[0].id == 10
    assert response.questions[0].source_document_id == 10
    assert response.questions[0].source_page_number == 1
    assert len(response.questions[0].options) == 4


def test_assessment_service_requires_ready_documents(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    db_session.add(make_document(user=user, status="uploaded"))
    db_session.commit()

    service = AssessmentService(
        db=db_session,
        settings=make_settings(),
        assessment_agent=FakeAssessmentAgent(),
        retriever_tool=FakeRetrieverTool(),
    )

    with pytest.raises(AssessmentDocumentsNotFoundError):
        service.generate_assessment(current_user=user, request=make_request())


def test_assessment_service_rejects_unknown_source_ref(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    db_session.add(make_document(user=user))
    db_session.commit()

    service = AssessmentService(
        db=db_session,
        settings=make_settings(),
        assessment_agent=FakeAssessmentAgent(draft=make_draft("SOURCE_999")),
        retriever_tool=FakeRetrieverTool(),
    )

    with pytest.raises(AssessmentGenerationInvalidOutputError):
        service.generate_assessment(current_user=user, request=make_request())


def test_assessment_service_lists_assessments(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    db_session.add(make_document(user=user))
    db_session.commit()

    service = AssessmentService(
        db=db_session,
        settings=make_settings(),
        assessment_agent=FakeAssessmentAgent(),
        retriever_tool=FakeRetrieverTool(),
    )
    service.generate_assessment(current_user=user, request=make_request())

    response = service.list_assessments(
        current_user=user,
        page=1,
        page_size=10,
        sort="newest",
    )

    assert response.total == 1
    assert response.total_pages == 1
    assert response.items[0].title == "Evaluation RAG"
