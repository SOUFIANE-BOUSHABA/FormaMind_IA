from __future__ import annotations

from app.schemas.rag import RetrievedChunk
from app.tools.assessment_context_tool import AssessmentContextTool


class FakeRetrieverTool:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.calls: list[dict[str, object]] = []

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        self.calls.append(
            {
                "user_id": user_id,
                "document_ids": document_ids,
                "question": question,
            }
        )
        return self.chunks


def make_chunk(
    *,
    vector_id: str = "document-10-page-2-chunk-0",
    document_id: int = 10,
    document_title: str = "Cours RAG",
    page_number: int = 2,
    text: str = "Le RAG combine recherche documentaire et génération.",
) -> RetrievedChunk:
    return RetrievedChunk(
        vector_id=vector_id,
        user_id=7,
        document_id=document_id,
        document_title=document_title,
        page_number=page_number,
        chunk_index=0,
        text=text,
        score=0.91,
    )


def test_assessment_context_tool_scopes_retrieval_to_user_and_documents() -> None:
    retriever = FakeRetrieverTool([make_chunk()])
    tool = AssessmentContextTool(
        user_id=7,
        document_ids=[10, 11],
        retriever_tool=retriever,
    )

    result = tool._run(topic="RAG", difficulty="intermediate")

    assert retriever.calls == [
        {
            "user_id": 7,
            "document_ids": [10, 11],
            "question": "RAG niveau intermediate",
        }
    ]
    assert "SOURCE_1" in result
    assert "document_id: 10" in result
    assert "document_title: Cours RAG" in result
    assert "page_number: 2" in result
    assert "Le RAG combine recherche documentaire" in result
    assert tool.source_map["SOURCE_1"].document_id == 10


def test_assessment_context_tool_keeps_stable_refs_for_repeated_chunks() -> None:
    chunk = make_chunk()
    retriever = FakeRetrieverTool([chunk])
    tool = AssessmentContextTool(
        user_id=7,
        document_ids=[10],
        retriever_tool=retriever,
    )

    first_result = tool._run(topic="RAG", difficulty="intermediate")
    second_result = tool._run(topic="RAG avancé", difficulty="advanced")

    assert "SOURCE_1" in first_result
    assert "SOURCE_1" in second_result
    assert len(tool.source_map) == 1


def test_assessment_context_tool_returns_safe_message_when_no_context() -> None:
    retriever = FakeRetrieverTool([])
    tool = AssessmentContextTool(
        user_id=7,
        document_ids=[10],
        retriever_tool=retriever,
    )

    result = tool._run(topic="CNN", difficulty="beginner")

    assert "Aucun contexte fiable" in result
    assert tool.source_map == {}