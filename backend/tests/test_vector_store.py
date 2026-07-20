from __future__ import annotations

from pathlib import Path

from app.rag.vector_store import ChromaVectorStore
from app.schemas.rag import TextChunk


def make_chunk(
    *,
    user_id: int,
    document_id: int,
    chunk_index: int,
    text: str,
) -> TextChunk:
    return TextChunk(
        document_id=document_id,
        user_id=user_id,
        document_title=f"Document {document_id}",
        page_number=1,
        chunk_index=chunk_index,
        text=text,
    )


def test_vector_store_filters_by_user(tmp_path: Path) -> None:
    vector_store = ChromaVectorStore(persist_directory=str(tmp_path / "chroma"))

    chunks = [
        make_chunk(
            user_id=1,
            document_id=10,
            chunk_index=0,
            text="RAG utilise des documents.",
        ),
        make_chunk(
            user_id=2,
            document_id=10,
            chunk_index=1,
            text="Texte appartenant a un autre user.",
        ),
    ]
    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    results = vector_store.search(
        user_id=1,
        document_ids=[10],
        query_embedding=[1.0, 0.0],
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].user_id == 1
    assert results[0].text == "RAG utilise des documents."


def test_vector_store_filters_by_document_ids(tmp_path: Path) -> None:
    vector_store = ChromaVectorStore(persist_directory=str(tmp_path / "chroma"))

    chunks = [
        make_chunk(
            user_id=1,
            document_id=10,
            chunk_index=0,
            text="Document selectionne.",
        ),
        make_chunk(
            user_id=1,
            document_id=11,
            chunk_index=1,
            text="Document non selectionne.",
        ),
    ]
    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    results = vector_store.search(
        user_id=1,
        document_ids=[10],
        query_embedding=[1.0, 0.0],
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].document_id == 10
    assert results[0].text == "Document selectionne."


def test_vector_store_deletes_document_chunks(tmp_path: Path) -> None:
    vector_store = ChromaVectorStore(persist_directory=str(tmp_path / "chroma"))

    chunks = [
        make_chunk(
            user_id=1,
            document_id=10,
            chunk_index=0,
            text="Chunk a supprimer.",
        ),
        make_chunk(
            user_id=1,
            document_id=11,
            chunk_index=1,
            text="Chunk a conserver.",
        ),
    ]
    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    vector_store.delete_document_chunks(user_id=1, document_id=10)

    deleted_results = vector_store.search(
        user_id=1,
        document_ids=[10],
        query_embedding=[1.0, 0.0],
        top_k=5,
    )
    kept_results = vector_store.search(
        user_id=1,
        document_ids=[11],
        query_embedding=[0.0, 1.0],
        top_k=5,
    )

    assert deleted_results == []
    assert len(kept_results) == 1
    assert kept_results[0].document_id == 11


def test_vector_store_can_read_legacy_metadata(tmp_path: Path) -> None:
    vector_store = ChromaVectorStore(persist_directory=str(tmp_path / "chroma"))
    vector_store.collection.upsert(
        ids=["legacy-document-10-page-1-chunk-0"],
        embeddings=[[1.0, 0.0]],
        documents=["Legacy chunk about CNN convolution."],
        metadatas=[
            {
                "chunk_index": 0,
                "document_id": 10,
                "document_title": "CNN",
                "page_number": 1,
                "user_id": 1,
            }
        ],
    )

    results = vector_store.search(
        user_id=1,
        document_ids=[10],
        query_embedding=[1.0, 0.0],
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].document_id == 10
    assert results[0].user_id == 1
    assert results[0].text == "Legacy chunk about CNN convolution."
