from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from app.rag.retriever import RetrieverTool
from app.schemas.rag import RetrievedChunk


class AssessmentContextToolInput(BaseModel):
    topic: str = Field(
        min_length=1,
        max_length=200,
        description="Sujet ou objectif d'apprentissage à rechercher.",
    )
    difficulty: str = Field(
        min_length=1,
        max_length=40,
        description="Niveau de difficulté demandé.",
    )


class AssessmentContextTool(BaseTool):
    name: str = "AssessmentContextTool"
    description: str = (
        "Recherche dans les supports de formation sélectionnés pour trouver "
        "des extraits fiables utilisables afin de créer des questions "
        "d'évaluation. Utilise uniquement les documents déjà sélectionnés."
    )
    args_schema: type[BaseModel] = AssessmentContextToolInput

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

    def _run(self, topic: str, difficulty: str) -> str:
        query = f"{topic.strip()} niveau {difficulty.strip()}".strip()
        chunks = self._retriever_tool.search(
            user_id=self._user_id,
            document_ids=self._document_ids,
            question=query,
        )

        if not chunks:
            return (
                "Aucun contexte fiable trouvé dans les documents sélectionnés "
                "pour ce sujet."
            )

        formatted_sources: list[str] = []

        for chunk in chunks:
            source_ref = self._source_ref_for_chunk(chunk)
            formatted_sources.append(self._format_source(source_ref, chunk))

        return "\n\n".join(formatted_sources)

    def _source_ref_for_chunk(self, chunk: RetrievedChunk) -> str:
        existing_ref = self._vector_id_to_source_ref.get(chunk.vector_id)
        if existing_ref is not None:
            return existing_ref

        source_ref = f"SOURCE_{self._next_source_index}"
        self._next_source_index += 1
        self._vector_id_to_source_ref[chunk.vector_id] = source_ref
        self._source_map[source_ref] = chunk
        return source_ref

    def _format_source(self, source_ref: str, chunk: RetrievedChunk) -> str:
        return "\n".join(
            [
                source_ref,
                f"document_id: {chunk.document_id}",
                f"document_title: {chunk.document_title}",
                f"page_number: {chunk.page_number}",
                f"excerpt: {self._excerpt(chunk.text)}",
                "content:",
                chunk.text,
            ]
        )

    def _excerpt(self, text: str) -> str:
        normalized = " ".join(text.split())
        return normalized[:300]
