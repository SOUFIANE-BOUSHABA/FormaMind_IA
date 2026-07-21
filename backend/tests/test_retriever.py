from __future__ import annotations

from typing import Any

from app.rag.retriever import RetrieverTool
from app.schemas.rag import RetrievedChunk


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.questions: list[str] = []

    def embed_query(self, question: str) -> list[float]:
        self.questions.append(question)
        return [0.1, 0.2]


class FakeVectorStore:
    def __init__(self, relevance_score: float | None = 0.9) -> None:
        self.calls: list[dict[str, Any]] = []
        self.relevance_score = relevance_score

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        self.calls.append(
            {
                "user_id": user_id,
                "document_ids": document_ids,
                "query_embedding": query_embedding,
                "top_k": top_k,
            }
        )
        return [
            RetrievedChunk(
                document_id=10,
                user_id=user_id,
                document_title="Cours RAG",
                page_number=2,
                chunk_index=0,
                text="Le RAG combine recherche et generation.",
                relevance_score=self.relevance_score,
            )
        ]


def test_retriever_embeds_question_and_queries_vector_store() -> None:
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()
    retriever = RetrieverTool(
        embedding_service=embedding_service,
        vector_store=vector_store,
        top_k=3,
    )

    chunks = retriever.search(
        user_id=5,
        document_ids=[10, 11],
        question=" Explique le RAG ",
    )

    assert embedding_service.questions == ["Explique le RAG"]
    assert vector_store.calls == [
        {
            "user_id": 5,
            "document_ids": [10, 11],
            "query_embedding": [0.1, 0.2],
            "top_k": 3,
        }
    ]
    assert len(chunks) == 1
    assert chunks[0].document_id == 10
    assert chunks[0].page_number == 2


def test_retriever_returns_empty_list_for_blank_question() -> None:
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()
    retriever = RetrieverTool(
        embedding_service=embedding_service,
        vector_store=vector_store,
        top_k=3,
    )

    chunks = retriever.search(
        user_id=5,
        document_ids=[10],
        question="   ",
    )

    assert chunks == []
    assert embedding_service.questions == []
    assert vector_store.calls == []


def test_retriever_filters_chunks_below_relevance_threshold() -> None:
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore(relevance_score=0.18)
    retriever = RetrieverTool(
        embedding_service=embedding_service,
        min_relevance_score=0.24,
        vector_store=vector_store,
        top_k=3,
    )

    chunks = retriever.search(
        user_id=5,
        document_ids=[10],
        question="Question hors sujet",
    )

    assert chunks == []
