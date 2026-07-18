from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DocumentStatus = Literal["uploaded", "processing", "ready", "failed"]
DocumentSort = Literal["newest", "oldest", "title_asc", "title_desc"]


class DocumentRead(BaseModel):
    id: int
    title: str
    original_filename: str
    mime_type: str
    file_size: int
    page_count: int
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class DocumentUploadResponse(DocumentRead):
    pass
