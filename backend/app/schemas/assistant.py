from __future__ import annotations

from pydantic import BaseModel, Field

NO_CONTEXT_ANSWER = (
    "Je n'ai pas trouvé suffisamment d'informations dans les documents "
    "sélectionnés pour répondre à cette question."
)


class AskQuestionRequest(BaseModel):
    document_ids: list[int] = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)


class SourceCitation(BaseModel):
    document_id: int
    document_title: str
    page_number: int = Field(ge=1)
    excerpt: str = Field(min_length=1)


class KnowledgeAnswer(BaseModel):
    answer: str
    has_sufficient_context: bool
    sources: list[SourceCitation] = Field(default_factory=list)


class AskQuestionResponse(KnowledgeAnswer):
    pass
