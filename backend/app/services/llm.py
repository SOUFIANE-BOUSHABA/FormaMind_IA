from __future__ import annotations

import json
import logging

from google import genai
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.assistant import NO_CONTEXT_ANSWER, KnowledgeAnswer
from app.schemas.rag import RetrievedChunk

logger = logging.getLogger(__name__)


class LlmConfigurationError(Exception):
    pass


class LlmProviderError(Exception):
    pass


class GeminiLlmService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def generate_grounded_answer(
        self,
        *,
        question: str,
        contexts: list[RetrievedChunk],
    ) -> KnowledgeAnswer:
        if not self.settings.gemini_api_key or not self.settings.gemini_model:
            raise LlmConfigurationError

        if not contexts:
            return KnowledgeAnswer(
                answer=NO_CONTEXT_ANSWER,
                has_sufficient_context=False,
                sources=[],
            )

        prompt = self._build_prompt(question=question, contexts=contexts)

        try:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            logger.exception("Gemini provider request failed: %s", exc)
            raise LlmProviderError from exc

        try:
            return self._parse_response(response_text=response.text, contexts=contexts)
        except LlmProviderError:
            logger.exception("Gemini response could not be parsed as grounded JSON.")
            raise

    def _build_prompt(self, *, question: str, contexts: list[RetrievedChunk]) -> str:
        context_blocks = []

        for index, context in enumerate(contexts, start=1):
            context_blocks.append(
                "\n".join(
                    [
                        f"[SOURCE {index}]",
                        f"Document ID: {context.document_id}",
                        f"Document title: {context.document_title}",
                        f"Page: {context.page_number}",
                        f"Excerpt: {context.text}",
                    ]
                )
            )

        joined_context = "\n\n".join(context_blocks)

        return f"""
Tu es le Knowledge Agent de FormaMind AI.

Règles strictes:
- Réponds uniquement avec les sources fournies.
- N'utilise aucune connaissance externe.
- Si les sources ne suffisent pas, réponds exactement avec:
"{NO_CONTEXT_ANSWER}"
- Cite uniquement les sources réellement utilisées.
- Réponds en français.
- Retourne uniquement un JSON valide.

Format JSON attendu:
{{
  "answer": "réponse",
  "has_sufficient_context": true,
  "sources": [
    {{
      "document_id": 1,
      "document_title": "Titre",
      "page_number": 1,
      "excerpt": "court extrait"
    }}
  ]
}}

Question:
{question}

Sources:
{joined_context}
""".strip()

    def _parse_response(
        self,
        *,
        response_text: str | None,
        contexts: list[RetrievedChunk],
    ) -> KnowledgeAnswer:
        if not response_text:
            raise LlmProviderError

        cleaned_response = self._strip_json_fence(response_text)

        try:
            payload = json.loads(cleaned_response)
            answer = KnowledgeAnswer.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LlmProviderError from exc

        valid_sources = self._build_valid_sources(contexts)

        filtered_sources = [
            source
            for source in answer.sources
            if (source.document_id, source.page_number) in valid_sources
        ]

        if not answer.has_sufficient_context:
            return KnowledgeAnswer(
                answer=NO_CONTEXT_ANSWER,
                has_sufficient_context=False,
                sources=[],
            )

        if not filtered_sources:
            return KnowledgeAnswer(
                answer=NO_CONTEXT_ANSWER,
                has_sufficient_context=False,
                sources=[],
            )

        return KnowledgeAnswer(
            answer=answer.answer,
            has_sufficient_context=True,
            sources=filtered_sources,
        )

    def _strip_json_fence(self, response_text: str) -> str:
        cleaned = response_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json").strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```").strip()

        if cleaned.endswith("```"):
            cleaned = cleaned.removesuffix("```").strip()

        return cleaned

    def _build_valid_sources(
        self,
        contexts: list[RetrievedChunk],
    ) -> set[tuple[int, int]]:
        return {(context.document_id, context.page_number) for context in contexts}
