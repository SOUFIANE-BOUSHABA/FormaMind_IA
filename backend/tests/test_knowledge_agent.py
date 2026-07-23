from __future__ import annotations

from app.agents.grounding import CitationVerifier
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.memory import AgentMemoryStore
from app.schemas.assistant import NO_CONTEXT_ANSWER, KnowledgeAnswer, SourceCitation
from app.schemas.rag import RetrievedChunk


class FakeRetrieverTool:
    def __init__(self, responses: list[list[RetrievedChunk]]) -> None:
        self.responses = responses
        self.calls: list[tuple[int, list[int], str]] = []

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        self.calls.append((user_id, document_ids, question))
        if not self.responses:
            return []
        return self.responses.pop(0)


class FakeLlmService:
    def __init__(self, answer: KnowledgeAnswer | None = None) -> None:
        self.answer = answer
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    def generate_grounded_answer(
        self,
        *,
        question: str,
        contexts: list[RetrievedChunk],
    ) -> KnowledgeAnswer:
        self.calls.append((question, contexts))
        if self.answer is not None:
            return self.answer
        return make_answer(
            "Le RAG combine recherche documentaire et generation sourcee.",
        )


class FakeSequentialLlmService:
    def __init__(self, answers: list[KnowledgeAnswer]) -> None:
        self.answers = answers
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    def generate_grounded_answer(
        self,
        *,
        question: str,
        contexts: list[RetrievedChunk],
    ) -> KnowledgeAnswer:
        self.calls.append((question, contexts))
        return self.answers.pop(0)


def make_context(
    *,
    relevance_score: float = 0.9,
    text: str = "Le RAG combine recherche documentaire et generation sourcee.",
) -> RetrievedChunk:
    return RetrievedChunk(
        document_id=10,
        user_id=5,
        document_title="Cours RAG",
        page_number=2,
        chunk_index=0,
        text=text,
        relevance_score=relevance_score,
    )


def make_answer(answer: str) -> KnowledgeAnswer:
    return KnowledgeAnswer(
        answer=answer,
        has_sufficient_context=True,
        sources=[
            SourceCitation(
                document_id=10,
                document_title="Cours RAG",
                page_number=2,
                excerpt="Le RAG combine recherche documentaire et generation.",
            )
        ],
    )


def test_direct_factual_question_uses_retrieval_once() -> None:
    context = make_context()
    retriever = FakeRetrieverTool(responses=[[context]])
    llm_service = FakeLlmService()
    agent = KnowledgeAgent(retriever_tool=retriever, llm_service=llm_service)

    answer = agent.answer(user_id=5, document_ids=[10], question="C'est quoi RAG ?")

    assert answer.has_sufficient_context is True
    assert retriever.calls == [(5, [10], "C'est quoi RAG ?")]
    assert llm_service.calls == [("C'est quoi RAG ?", [context])]
    assert agent.last_state is not None
    assert agent.last_state.selected_strategy == "direct_retrieval"
    assert agent.last_state.retrieval_attempts[0].sufficient is True


def test_vague_follow_up_uses_memory_to_build_effective_question() -> None:
    context = make_context()
    retriever = FakeRetrieverTool(responses=[[context], [context]])
    llm_service = FakeLlmService()
    memory_store = AgentMemoryStore()
    agent = KnowledgeAgent(
        retriever_tool=retriever,
        llm_service=llm_service,
        memory_store=memory_store,
    )

    agent.answer(user_id=5, document_ids=[10], question="C'est quoi RAG ?")
    answer = agent.answer(user_id=5, document_ids=[10], question="explique plus")

    assert answer.has_sufficient_context is True
    assert retriever.calls == [(5, [10], "C'est quoi RAG ?")]
    assert "Question precedente: C'est quoi RAG ?" in llm_service.calls[1][0]
    assert "Nouvelle demande de suivi: explique plus" in llm_service.calls[1][0]
    assert llm_service.calls[1][1] == [context]
    assert agent.last_state is not None
    assert agent.last_state.selected_strategy == "memory_follow_up"


def test_accented_resume_follow_up_uses_memory() -> None:
    context = make_context()
    retriever = FakeRetrieverTool(responses=[[context], [context]])
    llm_service = FakeLlmService()
    agent = KnowledgeAgent(
        retriever_tool=retriever,
        llm_service=llm_service,
        memory_store=AgentMemoryStore(),
    )

    agent.answer(user_id=5, document_ids=[10], question="convolution ?")
    answer = agent.answer(user_id=5, document_ids=[10], question="r\u00e9sume \u00e7a")

    assert answer.has_sufficient_context is True
    assert retriever.calls == [(5, [10], "convolution ?")]
    assert agent.last_state is not None
    assert agent.last_state.selected_strategy == "memory_follow_up"


def test_follow_up_reuses_remembered_context_when_retrieval_is_weak() -> None:
    context = make_context(
        text="La convolution utilise un filtre qui glisse sur une image.",
    )
    retriever = FakeRetrieverTool(
        responses=[
            [context],
            [],
            [],
            [],
            [],
        ]
    )
    llm_service = FakeLlmService(
        make_answer("La convolution utilise un filtre qui glisse sur une image.")
    )
    agent = KnowledgeAgent(
        retriever_tool=retriever,
        llm_service=llm_service,
        memory_store=AgentMemoryStore(),
    )

    agent.answer(user_id=5, document_ids=[10], question="convolution ?")
    answer = agent.answer(user_id=5, document_ids=[10], question="explique plus ?")

    assert answer.has_sufficient_context is True
    assert retriever.calls == [(5, [10], "convolution ?")]
    assert llm_service.calls[1][1] == [context]
    assert agent.last_state is not None
    assert agent.last_state.selected_strategy == "memory_follow_up"
    assert agent.last_state.refusal_reason is None


def test_follow_up_uses_previous_answer_if_llm_returns_no_context() -> None:
    context = make_context(
        text="La convolution utilise un filtre qui glisse sur une image.",
    )
    first_answer = make_answer(
        "La convolution utilise un filtre qui glisse sur une image."
    )
    no_context_answer = KnowledgeAnswer(
        answer=NO_CONTEXT_ANSWER,
        has_sufficient_context=False,
        sources=[],
    )
    retriever = FakeRetrieverTool(responses=[[context]])
    llm_service = FakeSequentialLlmService([first_answer, no_context_answer])
    agent = KnowledgeAgent(
        retriever_tool=retriever,
        llm_service=llm_service,
        memory_store=AgentMemoryStore(),
    )

    agent.answer(user_id=5, document_ids=[10], question="convolution ?")
    answer = agent.answer(user_id=5, document_ids=[10], question="explique plus ?")

    assert answer == first_answer
    assert answer.has_sufficient_context is True
    assert retriever.calls == [(5, [10], "convolution ?")]


def test_weak_context_triggers_query_reformulation_retry() -> None:
    weak_context = make_context(relevance_score=0.25)
    strong_context = make_context(
        relevance_score=0.84,
        text="Le RAG recupere des passages pertinents puis genere une reponse.",
    )
    retriever = FakeRetrieverTool(responses=[[weak_context], [strong_context]])
    llm_service = FakeLlmService(
        make_answer("Le RAG recupere des passages et genere une reponse.")
    )
    agent = KnowledgeAgent(retriever_tool=retriever, llm_service=llm_service)

    answer = agent.answer(user_id=5, document_ids=[10], question="C'est quoi RAG ?")

    assert answer.has_sufficient_context is True
    assert len(retriever.calls) == 2
    assert retriever.calls[1][2] == "rag"
    assert llm_service.calls == [("C'est quoi RAG ?", [strong_context])]
    assert agent.last_state is not None
    assert agent.last_state.retrieval_attempts[0].sufficient is False
    assert agent.last_state.retrieval_attempts[1].sufficient is True


def test_no_reliable_context_returns_no_context_answer_without_llm_call() -> None:
    retriever = FakeRetrieverTool(responses=[[], []])
    llm_service = FakeLlmService()
    agent = KnowledgeAgent(retriever_tool=retriever, llm_service=llm_service)

    answer = agent.answer(user_id=5, document_ids=[10], question="Question externe ?")

    assert answer.answer == NO_CONTEXT_ANSWER
    assert answer.has_sufficient_context is False
    assert answer.sources == []
    assert llm_service.calls == []
    assert agent.last_state is not None
    assert agent.last_state.refusal_reason == "no_reliable_context"


def test_citation_verifier_rejects_unsupported_answer() -> None:
    context = make_context()
    unsupported_answer = make_answer(
        "La capitale du Maroc est Rabat et cette phrase n'est pas dans le cours."
    )
    retriever = FakeRetrieverTool(responses=[[context]])
    llm_service = FakeLlmService(unsupported_answer)
    agent = KnowledgeAgent(retriever_tool=retriever, llm_service=llm_service)

    answer = agent.answer(user_id=5, document_ids=[10], question="Question externe ?")

    assert answer.answer == NO_CONTEXT_ANSWER
    assert answer.has_sufficient_context is False
    assert answer.sources == []
    assert agent.last_state is not None
    assert agent.last_state.refusal_reason == "ungrounded_answer"


def test_empty_memory_does_not_crash_follow_up() -> None:
    retriever = FakeRetrieverTool(responses=[[]])
    llm_service = FakeLlmService()
    agent = KnowledgeAgent(
        retriever_tool=retriever,
        llm_service=llm_service,
        memory_store=AgentMemoryStore(),
    )

    answer = agent.answer(user_id=5, document_ids=[10], question="explique plus")

    assert answer.answer == NO_CONTEXT_ANSWER
    assert answer.has_sufficient_context is False
    assert retriever.calls[0][2] == "explique plus"


def test_citation_verifier_rejects_source_that_was_not_retrieved() -> None:
    context = make_context()
    answer = KnowledgeAnswer(
        answer="Le RAG combine recherche documentaire et generation sourcee.",
        has_sufficient_context=True,
        sources=[
            SourceCitation(
                document_id=99,
                document_title="Autre document",
                page_number=1,
                excerpt="Citation non recuperee.",
            )
        ],
    )

    assert CitationVerifier().is_grounded(answer=answer, contexts=[context]) is False
