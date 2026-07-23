from __future__ import annotations

from app.agents.decision_policy import AgentDecisionPolicy
from app.agents.grounding import CitationVerifier
from app.agents.memory import AgentMemoryStore, ConversationTurn
from app.rag.retriever import RetrieverTool
from app.schemas.agent import KnowledgeAgentState, RetrievalAttempt
from app.schemas.assistant import NO_CONTEXT_ANSWER, KnowledgeAnswer
from app.schemas.rag import RetrievedChunk
from app.services.llm import GeminiLlmService


class KnowledgeAgent:
    role = "Specialiste des connaissances pedagogiques"
    goal = (
        "Repondre uniquement a partir des supports selectionnes, "
        "prendre des decisions de retrieval, utiliser une memoire courte "
        "et verifier les citations avant de repondre."
    )

    def __init__(
        self,
        *,
        retriever_tool: RetrieverTool,
        llm_service: GeminiLlmService,
        memory_store: AgentMemoryStore | None = None,
        decision_policy: AgentDecisionPolicy | None = None,
        citation_verifier: CitationVerifier | None = None,
    ) -> None:
        self.retriever_tool = retriever_tool
        self.llm_service = llm_service
        self.memory_store = memory_store or AgentMemoryStore()
        self.decision_policy = decision_policy or AgentDecisionPolicy()
        self.citation_verifier = citation_verifier or CitationVerifier()
        self.last_state: KnowledgeAgentState | None = None

    def answer(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> KnowledgeAnswer:
        memory_key = self.memory_store.conversation_key(
            user_id=user_id,
            document_ids=document_ids,
        )
        latest_turn = self.memory_store.latest_successful_turn(memory_key)
        effective_question, strategy = self.decision_policy.build_effective_question(
            question=question,
            latest_turn=latest_turn,
        )
        state = KnowledgeAgentState(
            selected_strategy=strategy,
            original_question=question,
            effective_question=effective_question,
        )

        if strategy == "memory_follow_up" and latest_turn is not None:
            contexts = latest_turn.contexts
            state.confidence = self.decision_policy.confidence_for(contexts)
        else:
            contexts = self._retrieve_with_decisions(
                user_id=user_id,
                document_ids=document_ids,
                question=effective_question,
                state=state,
            )

        if not contexts:
            answer = self._refuse(state=state, reason="no_reliable_context")
            self._remember(memory_key, question, effective_question, answer, [])
            return answer

        answer = self.llm_service.generate_grounded_answer(
            question=effective_question,
            contexts=contexts,
        )
        if (
            not answer.has_sufficient_context
            and strategy == "memory_follow_up"
            and latest_turn is not None
        ):
            answer = latest_turn.answer

        if not self.citation_verifier.is_grounded(answer=answer, contexts=contexts):
            answer = self._refuse(state=state, reason="ungrounded_answer")
            self._remember(memory_key, question, effective_question, answer, [])
            return answer

        state.confidence = self.decision_policy.confidence_for(contexts)
        state.selected_source_ids = self.citation_verifier.selected_source_ids(
            answer=answer,
            contexts=contexts,
        )
        self.last_state = state
        self._remember(memory_key, question, effective_question, answer, contexts)
        return answer

    def _retrieve_with_decisions(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
        state: KnowledgeAgentState,
    ) -> list[RetrievedChunk]:
        best_contexts: list[RetrievedChunk] = []
        state.query_variants = self.decision_policy.query_variants(question)

        for query in state.query_variants:
            contexts = self.retriever_tool.search(
                user_id=user_id,
                document_ids=document_ids,
                question=query,
            )
            sufficient = self.decision_policy.has_sufficient_context(contexts)
            state.retrieval_attempts.append(
                RetrievalAttempt(
                    query=query,
                    context_count=len(contexts),
                    best_relevance_score=self.decision_policy.best_relevance_score(
                        contexts
                    ),
                    sufficient=sufficient,
                )
            )

            if self._is_better_context(contexts, best_contexts):
                best_contexts = contexts

            if sufficient:
                self.last_state = state
                return contexts

        state.confidence = self.decision_policy.confidence_for(best_contexts)
        self.last_state = state
        return []

    def _is_better_context(
        self,
        candidate: list[RetrievedChunk],
        current: list[RetrievedChunk],
    ) -> bool:
        candidate_score = self.decision_policy.best_relevance_score(candidate) or 0
        current_score = self.decision_policy.best_relevance_score(current) or 0
        if candidate_score == current_score:
            return len(candidate) > len(current)
        return candidate_score > current_score

    def _refuse(self, *, state: KnowledgeAgentState, reason: str) -> KnowledgeAnswer:
        state.refusal_reason = reason
        state.confidence = "low"
        self.last_state = state
        return KnowledgeAnswer(
            answer=NO_CONTEXT_ANSWER,
            has_sufficient_context=False,
            sources=[],
        )

    def _remember(
        self,
        memory_key: str,
        question: str,
        effective_question: str,
        answer: KnowledgeAnswer,
        contexts: list[RetrievedChunk],
    ) -> None:
        self.memory_store.remember(
            memory_key,
            ConversationTurn(
                user_question=question,
                effective_question=effective_question,
                answer=answer,
                contexts=contexts,
            ),
        )
