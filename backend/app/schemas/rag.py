from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    document_id: int
    user_id: int
    document_title: str
    page_number: int = Field(ge=1)
    text: str = Field(min_length=1)


class TextChunk(BaseModel):
    document_id: int
    user_id: int
    document_title: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)

    @property
    def vector_id(self) -> str:
        return (
            f"document-{self.document_id}"
            f"-page-{self.page_number}"
            f"-chunk-{self.chunk_index}"
        )


class RetrievedChunk(TextChunk):
    relevance_score: float | None = None


class ProcessDocumentResponse(BaseModel):
    document_id: int
    status: str
    page_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    message: str
