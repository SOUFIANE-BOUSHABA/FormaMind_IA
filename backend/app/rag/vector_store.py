from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from llama_index.core.schema import MetadataMode, TextNode
from llama_index.core.vector_stores import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
)
from llama_index.vector_stores.chroma import ChromaVectorStore as LlamaChromaVectorStore

from app.schemas.rag import RetrievedChunk, TextChunk

COLLECTION_NAME = "formamind_course_chunks"


class VectorStoreError(Exception):
    pass


USER_METADATA_KEY = "formamind_user_id"
DOCUMENT_METADATA_KEY = "formamind_document_id"
LEGACY_USER_METADATA_KEY = "user_id"
LEGACY_DOCUMENT_METADATA_KEY = "document_id"


class ChromaVectorStore:
    def __init__(self, *, persist_directory: str) -> None:
        self.persist_directory = persist_directory
        self.client = self._create_client_with_recovery()
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        self.vector_store = LlamaChromaVectorStore(
            chroma_collection=self.collection,
        )

    def _create_client_with_recovery(self) -> Any:
        try:
            return chromadb.PersistentClient(path=self.persist_directory)
        except BaseException as exc:
            if not self._is_chroma_panic(exc):
                raise VectorStoreError from exc

            self._quarantine_corrupted_store()
            try:
                return chromadb.PersistentClient(path=self.persist_directory)
            except BaseException as retry_exc:
                raise VectorStoreError from retry_exc

    def _is_chroma_panic(self, exc: BaseException) -> bool:
        return (
            exc.__class__.__module__.startswith("pyo3_runtime")
            or "RustBindingsAPI" in str(exc)
            or "range start index" in str(exc)
        )

    def _quarantine_corrupted_store(self) -> None:
        store_path = Path(self.persist_directory)
        if not store_path.exists():
            return

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        backup_path = store_path.with_name(f"{store_path.name}_corrupt_{timestamp}")
        shutil.move(str(store_path), str(backup_path))

    def upsert_chunks(
        self,
        *,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            msg = "chunks and embeddings must have the same length."
            raise VectorStoreError(msg)

        try:
            nodes = [
                TextNode(
                    id_=chunk.vector_id,
                    text=chunk.text,
                    embedding=embeddings[index],
                    metadata=self._metadata_from_chunk(chunk),
                )
                for index, chunk in enumerate(chunks)
            ]
            self.vector_store.add(nodes)
        except Exception as exc:
            raise VectorStoreError from exc

    def delete_document_chunks(self, *, user_id: int, document_id: int) -> None:
        try:
            for user_key, document_key in self._metadata_key_pairs():
                self.collection.delete(
                    where={
                        "$and": [
                            {user_key: user_id},
                            {document_key: document_id},
                        ]
                    }
                )
        except Exception as exc:
            raise VectorStoreError from exc

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not document_ids or not query_embedding:
            return []

        chunks_by_vector_id: dict[str, RetrievedChunk] = {}

        for user_key, document_key in self._metadata_key_pairs():
            try:
                results = self.vector_store.query(
                    VectorStoreQuery(
                        query_embedding=query_embedding,
                        similarity_top_k=top_k,
                        filters=MetadataFilters(
                            filters=[
                                MetadataFilter(key=user_key, value=user_id),
                                MetadataFilter(
                                    key=document_key,
                                    operator=FilterOperator.IN,
                                    value=document_ids,
                                ),
                            ]
                        ),
                    )
                )
            except Exception as exc:
                raise VectorStoreError from exc

            for chunk in self._map_query_results(results):
                chunks_by_vector_id[chunk.vector_id] = chunk

        return sorted(
            chunks_by_vector_id.values(),
            key=lambda chunk: chunk.relevance_score or 0,
            reverse=True,
        )[:top_k]

    def _metadata_from_chunk(self, chunk: TextChunk) -> dict[str, str | int]:
        return {
            USER_METADATA_KEY: chunk.user_id,
            DOCUMENT_METADATA_KEY: chunk.document_id,
            "document_title": chunk.document_title,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
        }

    def _metadata_key_pairs(self) -> tuple[tuple[str, str], tuple[str, str]]:
        return (
            (USER_METADATA_KEY, DOCUMENT_METADATA_KEY),
            (LEGACY_USER_METADATA_KEY, LEGACY_DOCUMENT_METADATA_KEY),
        )

    def _metadata_value(
        self,
        metadata: dict[str, Any],
        *,
        current_key: str,
        legacy_key: str,
    ) -> Any:
        if current_key in metadata:
            return metadata[current_key]

        return metadata[legacy_key]

    def _map_query_results(self, results: Any) -> list[RetrievedChunk]:
        nodes = results.nodes or []
        similarities = results.similarities or []
        chunks: list[RetrievedChunk] = []

        for index, node in enumerate(nodes):
            metadata = node.metadata or {}
            similarity = similarities[index] if index < len(similarities) else None

            chunks.append(
                RetrievedChunk(
                    document_id=int(
                        self._metadata_value(
                            metadata,
                            current_key=DOCUMENT_METADATA_KEY,
                            legacy_key=LEGACY_DOCUMENT_METADATA_KEY,
                        )
                    ),
                    user_id=int(
                        self._metadata_value(
                            metadata,
                            current_key=USER_METADATA_KEY,
                            legacy_key=LEGACY_USER_METADATA_KEY,
                        )
                    ),
                    document_title=str(metadata["document_title"]),
                    page_number=int(metadata["page_number"]),
                    chunk_index=int(metadata["chunk_index"]),
                    text=node.get_content(metadata_mode=MetadataMode.NONE),
                    relevance_score=similarity,
                )
            )

        return chunks
