from __future__ import annotations

from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import ChromaVectorStore
from app.schemas.rag import RetrievedChunk


class RetrieverTool:
    def __init__(
        self,
        *,
        embedding_service: EmbeddingService,
        vector_store: ChromaVectorStore,
        top_k: int,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.top_k = top_k

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        cleaned_question = question.strip()
        if not cleaned_question:
            return []

        query_embedding = self.embedding_service.embed_query(cleaned_question)

        return self.vector_store.search(
            user_id=user_id,
            document_ids=document_ids,
            query_embedding=query_embedding,
            top_k=self.top_k,
        )
