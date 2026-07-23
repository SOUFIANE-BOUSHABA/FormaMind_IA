from __future__ import annotations

import re
import unicodedata

from app.agents.memory import ConversationTurn
from app.schemas.rag import RetrievedChunk


class AgentDecisionPolicy:
    follow_up_markers = {
        "ca",
        "ce point",
        "cette partie",
        "celle-ci",
        "detaille",
        "detailler",
        "deuxieme",
        "explique davantage",
        "explique plus",
        "it",
        "more",
        "resume",
        "resume ca",
        "second one",
        "summarize",
        "that",
    }

    def __init__(self, *, min_sufficient_score: float = 0.35) -> None:
        self.min_sufficient_score = min_sufficient_score

    def build_effective_question(
        self,
        *,
        question: str,
        latest_turn: ConversationTurn | None,
    ) -> tuple[str, str]:
        cleaned = " ".join(question.split())
        if latest_turn is None or not self._looks_like_follow_up(cleaned):
            return cleaned, "direct_retrieval"

        effective_question = (
            f"Question precedente: {latest_turn.effective_question}. "
            f"Nouvelle demande de suivi: {cleaned}"
        )
        return effective_question, "memory_follow_up"

    def query_variants(self, question: str) -> list[str]:
        cleaned = " ".join(question.split())
        previous_question, follow_up = self._follow_up_parts(cleaned)
        if previous_question is not None:
            return self._follow_up_query_variants(
                previous_question=previous_question,
                follow_up=follow_up,
            )

        keywords = self._keywords(cleaned)
        focused_query = " ".join(keywords[:8])
        variants = [cleaned]

        if focused_query and focused_query.lower() != cleaned.lower():
            variants.append(focused_query)

        variants.extend(
            [
                f"{cleaned} definition explication",
                f"{cleaned} points cles exemples",
            ]
        )
        return list(dict.fromkeys(variant for variant in variants if variant.strip()))

    def has_sufficient_context(self, contexts: list[RetrievedChunk]) -> bool:
        if not contexts:
            return False

        best_score = self.best_relevance_score(contexts)
        if best_score is None:
            return True
        return best_score >= self.min_sufficient_score

    def best_relevance_score(self, contexts: list[RetrievedChunk]) -> float | None:
        scores = [
            context.relevance_score
            for context in contexts
            if context.relevance_score is not None
        ]
        return max(scores) if scores else None

    def confidence_for(self, contexts: list[RetrievedChunk]) -> str:
        best_score = self.best_relevance_score(contexts)
        if best_score is None and contexts:
            return "medium"
        if best_score is None:
            return "low"
        if best_score >= 0.65:
            return "high"
        if best_score >= self.min_sufficient_score:
            return "medium"
        return "low"

    def _looks_like_follow_up(self, question: str) -> bool:
        normalized = self._normalize(question)
        return any(marker in normalized for marker in self.follow_up_markers)

    def _keywords(self, text: str) -> list[str]:
        stop_words = {
            "avec",
            "dans",
            "de",
            "demande",
            "des",
            "du",
            "est",
            "la",
            "le",
            "les",
            "nouvelle",
            "pour",
            "precedente",
            "que",
            "question",
            "qui",
            "quoi",
            "suivi",
            "sur",
            "un",
            "une",
        }
        words = re.findall(r"[\w]+", self._normalize(text))
        return [word for word in words if len(word) > 2 and word not in stop_words]

    def _follow_up_parts(self, question: str) -> tuple[str | None, str]:
        prefix = "Question precedente: "
        separator = ". Nouvelle demande de suivi: "
        if not question.startswith(prefix) or separator not in question:
            return None, question

        previous_question, follow_up = question.removeprefix(prefix).split(
            separator,
            maxsplit=1,
        )
        return previous_question.strip(), follow_up.strip()

    def _follow_up_query_variants(
        self,
        *,
        previous_question: str,
        follow_up: str,
    ) -> list[str]:
        previous_keywords = " ".join(self._keywords(previous_question)[:8])
        follow_up_keywords = " ".join(self._keywords(follow_up)[:4])
        variants = [
            previous_question,
            previous_keywords,
            f"{previous_question} {follow_up}",
            f"{previous_keywords} {follow_up_keywords}",
        ]
        return list(dict.fromkeys(variant for variant in variants if variant.strip()))

    def _normalize(self, text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text.lower())
        return "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )
