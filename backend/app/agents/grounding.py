from __future__ import annotations

import re

from app.schemas.assistant import KnowledgeAnswer
from app.schemas.rag import RetrievedChunk


class CitationVerifier:
    def __init__(self, *, min_answer_overlap: int = 3) -> None:
        self.min_answer_overlap = min_answer_overlap

    def is_grounded(
        self,
        *,
        answer: KnowledgeAnswer,
        contexts: list[RetrievedChunk],
    ) -> bool:
        if not answer.has_sufficient_context:
            return True

        if not contexts or not answer.sources:
            return False

        valid_sources = {
            (context.document_id, context.document_title, context.page_number)
            for context in contexts
        }
        for source in answer.sources:
            if (
                source.document_id,
                source.document_title,
                source.page_number,
            ) not in valid_sources:
                return False

        context_tokens = self._tokens(" ".join(context.text for context in contexts))
        answer_tokens = self._tokens(answer.answer)
        if not answer_tokens:
            return False

        shared_tokens = answer_tokens.intersection(context_tokens)
        return len(shared_tokens) >= min(self.min_answer_overlap, len(answer_tokens))

    def selected_source_ids(
        self,
        *,
        answer: KnowledgeAnswer,
        contexts: list[RetrievedChunk],
    ) -> list[str]:
        ids: list[str] = []
        for source in answer.sources:
            for context in contexts:
                if (
                    source.document_id == context.document_id
                    and source.page_number == context.page_number
                ):
                    ids.append(context.vector_id)
                    break
        return ids

    def _tokens(self, text: str) -> set[str]:
        stop_words = {
            "avec",
            "cette",
            "dans",
            "des",
            "donc",
            "elle",
            "est",
            "les",
            "plus",
            "pour",
            "que",
            "qui",
            "une",
            "vous",
        }
        return {
            token
            for token in re.findall(r"[\wÀ-ÿ]+", text.lower())
            if len(token) > 3 and token not in stop_words
        }
