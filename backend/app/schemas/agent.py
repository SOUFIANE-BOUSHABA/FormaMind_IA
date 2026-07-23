from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalAttempt(BaseModel):
    query: str
    context_count: int
    best_relevance_score: float | None
    sufficient: bool


class KnowledgeAgentState(BaseModel):
    selected_strategy: str
    original_question: str
    effective_question: str
    query_variants: list[str] = Field(default_factory=list)
    retrieval_attempts: list[RetrievalAttempt] = Field(default_factory=list)
    selected_source_ids: list[str] = Field(default_factory=list)
    confidence: str = "low"
    refusal_reason: str | None = None
