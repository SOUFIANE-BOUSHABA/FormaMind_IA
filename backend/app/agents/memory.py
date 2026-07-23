from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock

from app.schemas.assistant import KnowledgeAnswer
from app.schemas.rag import RetrievedChunk


@dataclass(frozen=True)
class ConversationTurn:
    user_question: str
    effective_question: str
    answer: KnowledgeAnswer
    contexts: list[RetrievedChunk]


class AgentMemoryStore:
    def __init__(self, *, max_turns: int = 6) -> None:
        self.max_turns = max_turns
        self._turns: dict[str, deque[ConversationTurn]] = {}
        self._lock = Lock()

    def conversation_key(self, *, user_id: int, document_ids: list[int]) -> str:
        normalized_documents = ",".join(str(item) for item in sorted(document_ids))
        return f"user:{user_id}:documents:{normalized_documents}"

    def recent_turns(self, key: str) -> list[ConversationTurn]:
        with self._lock:
            turns = self._turns.get(key)
            if turns is None:
                return []
            return list(turns)

    def latest_successful_turn(self, key: str) -> ConversationTurn | None:
        with self._lock:
            turns = list(self._turns.get(key) or deque())

        for turn in reversed(turns):
            if turn.answer.has_sufficient_context:
                return turn
        return None

    def remember(self, key: str, turn: ConversationTurn) -> None:
        with self._lock:
            if key not in self._turns:
                self._turns[key] = deque(maxlen=self.max_turns)
            self._turns[key].append(turn)

    def clear(self) -> None:
        with self._lock:
            self._turns.clear()
