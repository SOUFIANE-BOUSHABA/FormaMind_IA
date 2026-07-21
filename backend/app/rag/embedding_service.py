from __future__ import annotations

import os

from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class EmbeddingService:
    def __init__(self, *, model_name: str) -> None:
        self.model_name = model_name
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        self.model = HuggingFaceEmbedding(
            model_name=model_name,
            local_files_only=True,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        return self.model.get_text_embedding_batch(texts)

    def embed_query(self, question: str) -> list[float]:
        cleaned_question = question.strip()
        if not cleaned_question:
            return []

        return self.model.get_query_embedding(cleaned_question)
