from __future__ import annotations

from app.rag.retriever import RetrieverTool
from app.schemas.assistant import NO_CONTEXT_ANSWER, KnowledgeAnswer
from app.services.llm import GeminiLlmService


class KnowledgeAgent:
    role = "Spécialiste des connaissances pédagogiques"
    goal = (
        "Répondre uniquement à partir des supports sélectionnés "
        "et citer les pages utilisées."
    )

    def __init__(
        self,
        *,
        retriever_tool: RetrieverTool,
        llm_service: GeminiLlmService,
    ) -> None:
        self.retriever_tool = retriever_tool
        self.llm_service = llm_service

    def answer(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> KnowledgeAnswer:
        contexts = self.retriever_tool.search(
            user_id=user_id,
            document_ids=document_ids,
            question=question,
        )

        if not contexts:
            return KnowledgeAnswer(
                answer=NO_CONTEXT_ANSWER,
                has_sufficient_context=False,
                sources=[],
            )

        return self.llm_service.generate_grounded_answer(
            question=question,
            contexts=contexts,
        )
