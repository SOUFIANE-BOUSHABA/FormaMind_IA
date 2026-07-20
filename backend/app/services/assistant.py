from __future__ import annotations

from app.agents.knowledge_agent import KnowledgeAgent
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.schemas.assistant import AskQuestionRequest, AskQuestionResponse
from app.services.llm import LlmConfigurationError, LlmProviderError


class AssistantError(Exception):
    message = "Impossible d'interroger l'assistant pédagogique."


class SelectedDocumentsNotFoundError(AssistantError):
    message = "Un ou plusieurs documents sélectionnés sont introuvables."


class SelectedDocumentsNotReadyError(AssistantError):
    message = (
        "Les documents sélectionnés doivent être analysés avant d'être interrogés."
    )


class AssistantConfigurationError(AssistantError):
    message = "Le service d'intelligence artificielle n'est pas configuré."


class AssistantProviderError(AssistantError):
    message = "Le service d'intelligence artificielle est temporairement indisponible."


class AssistantService:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        knowledge_agent: KnowledgeAgent,
    ) -> None:
        self.document_repository = document_repository
        self.knowledge_agent = knowledge_agent

    def ask_question(
        self,
        *,
        user: User,
        request: AskQuestionRequest,
    ) -> AskQuestionResponse:
        unique_document_ids = list(dict.fromkeys(request.document_ids))
        documents = self.document_repository.list_owned_by_ids(
            document_ids=unique_document_ids,
            user_id=user.id,
        )

        if len(documents) != len(unique_document_ids):
            raise SelectedDocumentsNotFoundError

        if any(document.status != "ready" for document in documents):
            raise SelectedDocumentsNotReadyError

        try:
            answer = self.knowledge_agent.answer(
                user_id=user.id,
                document_ids=unique_document_ids,
                question=request.question,
            )
        except LlmConfigurationError as exc:
            raise AssistantConfigurationError from exc
        except LlmProviderError as exc:
            raise AssistantProviderError from exc

        return AskQuestionResponse.model_validate(answer.model_dump())
