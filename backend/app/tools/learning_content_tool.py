from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from app.rag.retriever import RetrieverTool
from app.schemas.rag import RetrievedChunk


class LearningContentToolInput(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    missing_concepts: list[str] = Field(default_factory=list, max_length=8)
    target_difficulty: str = Field(default="intermediate", max_length=40)
    desired_learning_objective: str = Field(min_length=1, max_length=240)


class LearningContentTool(BaseTool):
    name: str = "LearningContentTool"
    description: str = (
        "Recherche des extraits fiables dans les supports selectionnes pour "
        "alimenter les activites d'un plan d'apprentissage personnalise."
    )
    args_schema: type[BaseModel] = LearningContentToolInput

    _user_id: int = PrivateAttr()
    _document_ids: list[int] = PrivateAttr()
    _retriever_tool: RetrieverTool = PrivateAttr()
    _source_map: dict[str, RetrievedChunk] = PrivateAttr(default_factory=dict)
    _vector_id_to_source_ref: dict[str, str] = PrivateAttr(default_factory=dict)
    _next_source_index: int = PrivateAttr(default=1)

    def __init__(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        retriever_tool: RetrieverTool,
    ) -> None:
        super().__init__()
        self._user_id = user_id
        self._document_ids = document_ids
        self._retriever_tool = retriever_tool

    @property
    def source_map(self) -> dict[str, RetrievedChunk]:
        return dict(self._source_map)

    def _run(
        self,
        topic: str,
        missing_concepts: list[str] | None = None,
        target_difficulty: str = "intermediate",
        desired_learning_objective: str = "",
    ) -> str:
        concepts = missing_concepts or []
        query_parts = [
            topic.strip(),
            target_difficulty.strip(),
            desired_learning_objective.strip(),
            " ".join(concept.strip() for concept in concepts if concept.strip()),
        ]
        query = " ".join(part for part in query_parts if part)
        chunks = self._retriever_tool.search(
            user_id=self._user_id,
            document_ids=self._document_ids,
            question=query,
        )

        if not chunks:
            return json.dumps(
                {
                    "message": "Aucun contenu fiable trouve.",
                    "sources": [],
                },
                ensure_ascii=False,
            )

        sources = []
        for chunk in chunks:
            source_ref = self._source_ref_for_chunk(chunk)
            sources.append(
                {
                    "source_ref": source_ref,
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "page_number": chunk.page_number,
                    "excerpt": self._excerpt(chunk.text),
                }
            )

        return json.dumps({"sources": sources}, ensure_ascii=False, indent=2)

    def _source_ref_for_chunk(self, chunk: RetrievedChunk) -> str:
        existing_ref = self._vector_id_to_source_ref.get(chunk.vector_id)
        if existing_ref is not None:
            return existing_ref

        source_ref = f"CONTENT_SOURCE_{self._next_source_index}"
        self._next_source_index += 1
        self._vector_id_to_source_ref[chunk.vector_id] = source_ref
        self._source_map[source_ref] = chunk
        return source_ref

    def _excerpt(self, text: str) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= 420:
            return normalized
        return f"{normalized[:419].rstrip()}..."
