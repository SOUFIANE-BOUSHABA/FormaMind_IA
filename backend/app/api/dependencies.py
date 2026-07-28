from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.agents.memory import AgentMemoryStore
from app.core.auth_errors import InactiveUserError, InvalidAccessTokenError
from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.documents import DocumentService
from app.storage.documents import DocumentStorageService

bearer_scheme = HTTPBearer(auto_error=False)
_knowledge_agent_memory = AgentMemoryStore()


def get_app_settings() -> Settings:
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]


def get_vector_store(settings: AppSettings) -> Any:
    from app.rag.vector_store import ChromaVectorStore

    return ChromaVectorStore(
        persist_directory=settings.chroma_persist_directory,
    )


VectorStoreDependency = Annotated[Any, Depends(get_vector_store)]


def get_embedding_service(settings: AppSettings) -> Any:
    from app.rag.embedding_service import EmbeddingService

    return EmbeddingService(model_name=settings.embedding_model_name)


EmbeddingServiceDependency = Annotated[Any, Depends(get_embedding_service)]


def get_auth_service(db: DbSession, settings: AppSettings) -> AuthService:
    return AuthService(UserRepository(db), settings)


def get_document_service(
    db: DbSession,
    settings: AppSettings,
) -> DocumentService:
    return DocumentService(
        DocumentRepository(db),
        DocumentStorageService(
            upload_directory=settings.upload_directory,
            max_upload_size_mb=settings.max_upload_size_mb,
        ),
        vector_store_factory=lambda: get_vector_store(settings),
    )


def get_document_processing_service(
    db: DbSession,
    settings: AppSettings,
    vector_store: VectorStoreDependency,
    embedding_service: EmbeddingServiceDependency,
) -> Any:
    from app.rag.pdf_extractor import PdfTextExtractor
    from app.rag.text_chunker import TextChunker
    from app.services.document_processing import DocumentProcessingService

    return DocumentProcessingService(
        document_repository=DocumentRepository(db),
        storage_service=DocumentStorageService(
            upload_directory=settings.upload_directory,
            max_upload_size_mb=settings.max_upload_size_mb,
        ),
        pdf_extractor=PdfTextExtractor(),
        text_chunker=TextChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        ),
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def get_assistant_service(
    db: DbSession,
    settings: AppSettings,
    vector_store: VectorStoreDependency,
    embedding_service: EmbeddingServiceDependency,
) -> Any:
    from app.agents.knowledge_agent import KnowledgeAgent
    from app.rag.retriever import RetrieverTool
    from app.services.assistant import AssistantService
    from app.services.llm import GeminiLlmService

    retriever_tool = RetrieverTool(
        embedding_service=embedding_service,
        vector_store=vector_store,
        min_relevance_score=settings.rag_min_relevance_score,
        top_k=settings.rag_top_k,
    )
    llm_service = GeminiLlmService(settings=settings)
    knowledge_agent = KnowledgeAgent(
        retriever_tool=retriever_tool,
        llm_service=llm_service,
        memory_store=_knowledge_agent_memory,
    )
    return AssistantService(
        document_repository=DocumentRepository(db),
        knowledge_agent=knowledge_agent,
    )


def get_assessment_service(
    db: DbSession,
    settings: AppSettings,
    vector_store: VectorStoreDependency,
    embedding_service: EmbeddingServiceDependency,
) -> Any:
    from app.rag.retriever import RetrieverTool
    from app.services.assessment import AssessmentService

    retriever_tool = RetrieverTool(
        embedding_service=embedding_service,
        vector_store=vector_store,
        min_relevance_score=settings.rag_min_relevance_score,
        top_k=settings.assessment_context_top_k,
    )
    return AssessmentService(
        db=db,
        settings=settings,
        retriever_tool=retriever_tool,
    )


def get_attempt_service(
    db: DbSession,
    settings: AppSettings,
) -> Any:
    from app.agents.assessment_agent import AssessmentAgent
    from app.repositories.attempt import AttemptRepository
    from app.services.attempt import AttemptService

    return AttemptService(
        repository=AttemptRepository(db),
        assessment_agent=AssessmentAgent(settings),
    )


def get_learning_plan_service(
    db: DbSession,
    settings: AppSettings,
    vector_store: VectorStoreDependency,
    embedding_service: EmbeddingServiceDependency,
) -> Any:
    from app.agents.learning_coach_agent import LearningCoachAgent
    from app.rag.retriever import RetrieverTool
    from app.repositories.learning_plan import LearningPlanRepository
    from app.services.learning_plan import LearningPlanService

    retriever_tool = RetrieverTool(
        embedding_service=embedding_service,
        vector_store=vector_store,
        min_relevance_score=settings.rag_min_relevance_score,
        top_k=settings.learning_content_top_k,
    )
    return LearningPlanService(
        repository=LearningPlanRepository(db),
        learning_coach_agent=LearningCoachAgent(settings),
        retriever_tool=retriever_tool,
    )


def get_soutenance_session_service(
    db: DbSession,
    settings: AppSettings,
) -> Any:
    from app.agents.soutenance_coach_agent import SoutenanceCoachAgent
    from app.repositories.soutenance import SoutenanceRepository
    from app.services.soutenance import SoutenanceSessionService

    return SoutenanceSessionService(
        repository=SoutenanceRepository(db),
        soutenance_coach_agent=SoutenanceCoachAgent(settings),
        settings=settings,
    )


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
AssistantServiceDependency = Annotated[Any, Depends(get_assistant_service)]
AssessmentServiceDependency = Annotated[Any, Depends(get_assessment_service)]
AttemptServiceDependency = Annotated[Any, Depends(get_attempt_service)]
LearningPlanServiceDependency = Annotated[Any, Depends(get_learning_plan_service)]
SoutenanceSessionServiceDependency = Annotated[
    Any,
    Depends(get_soutenance_session_service),
]
DocumentProcessingServiceDependency = Annotated[
    Any,
    Depends(get_document_processing_service),
]
DocumentServiceDependency = Annotated[DocumentService, Depends(get_document_service)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def get_current_user(
    credentials: BearerCredentials,
    auth_service: AuthServiceDependency,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return auth_service.get_user_from_token(credentials.credentials)
    except (InvalidAccessTokenError, InactiveUserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[User, Depends(get_current_user)]
