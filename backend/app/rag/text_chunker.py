from __future__ import annotations

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from app.schemas.rag import ExtractedPage, TextChunk


class TextChunker:
    def __init__(self, *, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            msg = "chunk_size must be greater than 0."
            raise ValueError(msg)

        if chunk_overlap < 0:
            msg = "chunk_overlap cannot be negative."
            raise ValueError(msg)

        if chunk_overlap >= chunk_size:
            msg = "chunk_overlap must be smaller than chunk_size."
            raise ValueError(msg)

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            include_metadata=False,
        )

    def chunk_pages(self, pages: list[ExtractedPage]) -> list[TextChunk]:
        chunks: list[TextChunk] = []

        for page in pages:
            document = LlamaDocument(
                text=page.text,
            )
            nodes = self.splitter.get_nodes_from_documents([document])

            for node in nodes:
                chunk_text = node.text.strip()
                if not chunk_text:
                    continue

                chunks.append(
                    TextChunk(
                        document_id=page.document_id,
                        user_id=page.user_id,
                        document_title=page.document_title,
                        page_number=page.page_number,
                        chunk_index=len(chunks),
                        text=chunk_text,
                    )
                )

        return chunks
