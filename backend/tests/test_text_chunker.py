from __future__ import annotations

import pytest

from app.rag.text_chunker import TextChunker
from app.schemas.rag import ExtractedPage


def make_page(page_number: int, text: str) -> ExtractedPage:
    return ExtractedPage(
        document_id=1,
        user_id=2,
        document_title="Cours RAG",
        page_number=page_number,
        text=text,
    )


def test_chunker_respects_chunk_size() -> None:
    chunker = TextChunker(chunk_size=5, chunk_overlap=1)

    chunks = chunker.chunk_pages(
        [make_page(1, "one two three four five six seven eight nine ten")]
    )

    assert [chunk.text for chunk in chunks] == [
        "one two three four five",
        "five six seven eight nine",
        "nine ten",
    ]


def test_chunker_respects_overlap() -> None:
    chunker = TextChunker(chunk_size=6, chunk_overlap=2)

    chunks = chunker.chunk_pages(
        [make_page(1, "one two three four five six seven eight nine ten")]
    )

    assert [chunk.text for chunk in chunks] == [
        "one two three four five six",
        "five six seven eight nine ten",
    ]


def test_chunker_does_not_mix_pages() -> None:
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)

    chunks = chunker.chunk_pages(
        [
            make_page(1, "Texte de la page un"),
            make_page(2, "Texte de la page deux"),
        ]
    )

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[0].text == "Texte de la page un"
    assert chunks[1].page_number == 2
    assert chunks[1].text == "Texte de la page deux"


def test_chunker_uses_deterministic_chunk_indexes() -> None:
    chunker = TextChunker(chunk_size=5, chunk_overlap=1)

    chunks = chunker.chunk_pages(
        [
            make_page(1, "one two three four five six seven eight nine ten"),
            make_page(2, "alpha beta gamma delta epsilon zeta"),
        ]
    )

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3, 4]


def test_chunker_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be smaller"):
        TextChunker(chunk_size=100, chunk_overlap=100)
