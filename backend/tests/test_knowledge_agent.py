from __future__ import annotations

from app.agents.knowledge_agent import KnowledgeAgent
from app.schemas.assistant import NO_CONTEXT_ANSWER, KnowledgeAnswer, SourceCitation
from app.schemas.rag import RetrievedChunk


class FakeRetrieverTool:
    def __init__(self, contexts: list[RetrievedChunk]) -> None:
        self.contexts = contexts
        self.calls: list[tuple[int, list[int], str]] = []

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        self.calls.append((user_id, document_ids, question))
        return self.contexts


class FakeLlmService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    def generate_grounded_answer(
        self,
        *,
        question: str,
        contexts: list[RetrievedChunk],
    ) -> KnowledgeAnswer:
        self.calls.append((question, contexts))
        return KnowledgeAnswer(
            answer="Le RAG combine recherche et generation.",
            has_sufficient_context=True,
            sources=[
                SourceCitation(
                    document_id=10,
                    document_title="Cours RAG",
                    page_number=2,
                    excerpt="RAG combine recherche et generation.",
                )
            ],
        )


def make_context() -> RetrievedChunk:
    return RetrievedChunk(
        document_id=10,
        user_id=5,
        document_title="Cours RAG",
        page_number=2,
        chunk_index=0,
        text="Le RAG combine recherche et generation.",
        relevance_score=0.9,
    )


def test_knowledge_agent_returns_no_context_answer_without_chunks() -> None:
    retriever = FakeRetrieverTool(contexts=[])
    llm_service = FakeLlmService()
    agent = KnowledgeAgent(retriever_tool=retriever, llm_service=llm_service)

    answer = agent.answer(user_id=5, document_ids=[10], question="C'est quoi RAG ?")

    assert answer.answer == NO_CONTEXT_ANSWER
    assert answer.has_sufficient_context is False
    assert answer.sources == []
    assert llm_service.calls == []


def test_knowledge_agent_uses_retriever_then_llm() -> None:
    context = make_context()
    retriever = FakeRetrieverTool(contexts=[context])
    llm_service = FakeLlmService()
    agent = KnowledgeAgent(retriever_tool=retriever, llm_service=llm_service)

    answer = agent.answer(user_id=5, document_ids=[10], question="C'est quoi RAG ?")

    assert retriever.calls == [(5, [10], "C'est quoi RAG ?")]
    assert llm_service.calls == [("C'est quoi RAG ?", [context])]
    assert answer.has_sufficient_context is True
    assert answer.sources[0].document_id == 10
