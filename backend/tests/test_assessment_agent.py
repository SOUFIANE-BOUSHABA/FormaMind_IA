from __future__ import annotations

import pytest

from app.agents.assessment_agent import (
    AssessmentAgent,
    AssessmentAgentConfigurationError,
    AssessmentAgentOutputError,
)
from app.core.config import Settings
from app.schemas.assessment import AssessmentDraft, GenerateAssessmentRequest
from app.schemas.attempt import AssessmentCoachQuestionInput
from app.schemas.rag import RetrievedChunk


def make_settings(*, gemini_api_key: str | None = "test-key") -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite:///./test.db",
        access_token_secret="access-secret",
        refresh_token_secret="refresh-secret",
        gemini_api_key=gemini_api_key,
        gemini_model="gemini-2.0-flash",
    )


def make_request() -> GenerateAssessmentRequest:
    return GenerateAssessmentRequest(
        document_ids=[1],
        topics=["RAG"],
        difficulty="intermediate",
        question_count=3,
        question_types=["multiple_choice"],
    )


def make_five_question_request() -> GenerateAssessmentRequest:
    return GenerateAssessmentRequest(
        document_ids=[1],
        topics=["CNN"],
        difficulty="intermediate",
        question_count=5,
        question_types=["multiple_choice"],
    )


def make_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        vector_id="document-1-page-16-chunk-0",
        user_id=2,
        document_id=1,
        document_title="CNN",
        page_number=16,
        chunk_index=0,
        text=(
            "Dans une couche dense, chaque neurone est relie a tous les "
            "neurones de la couche precedente."
        ),
        score=0.92,
    )


def make_draft() -> AssessmentDraft:
    return AssessmentDraft(
        title="Evaluation RAG",
        difficulty="intermediate",
        questions=[
            {
                "type": "multiple_choice",
                "text": "Quel est le rôle principal du RAG ?",
                "options": [
                    {"text": "Chercher du contexte", "is_correct": True},
                    {"text": "Compresser des images", "is_correct": False},
                    {"text": "Compiler du code", "is_correct": False},
                    {"text": "Créer une base SQL", "is_correct": False},
                ],
                "correct_answer": "Chercher du contexte",
                "explanation": "Le RAG récupère un contexte avant la génération.",
                "points": 1,
                "source_ref": "SOURCE_1",
            },
            {
                "type": "multiple_choice",
                "text": "Pourquoi citer une source ?",
                "options": [
                    {"text": "Pour tracer la réponse", "is_correct": True},
                    {"text": "Pour masquer le contexte", "is_correct": False},
                    {"text": "Pour ignorer le document", "is_correct": False},
                    {"text": "Pour supprimer la réponse", "is_correct": False},
                ],
                "correct_answer": "Pour tracer la réponse",
                "explanation": "La citation relie la question au document.",
                "points": 1,
                "source_ref": "SOURCE_1",
            },
            {
                "type": "multiple_choice",
                "text": "Que doit éviter l'agent ?",
                "options": [
                    {"text": "Inventer une information", "is_correct": True},
                    {"text": "Utiliser le contexte", "is_correct": False},
                    {"text": "Citer une page", "is_correct": False},
                    {"text": "Respecter le niveau", "is_correct": False},
                ],
                "correct_answer": "Inventer une information",
                "explanation": "L'agent doit rester fondé sur les documents.",
                "points": 1,
                "source_ref": "SOURCE_1",
            },
        ],
    )


class FakeCrewResult:
    def __init__(
        self,
        *,
        pydantic: AssessmentDraft | None = None,
        raw: str | None = None,
    ) -> None:
        self.pydantic = pydantic
        self.raw = raw


def test_assessment_agent_requires_gemini_api_key() -> None:
    settings = make_settings(gemini_api_key="")
    settings.gemini_api_key = None
    agent = AssessmentAgent(settings)

    with pytest.raises(AssessmentAgentConfigurationError):
        agent.generate_assessment(
            request=make_request(),
            context_tool=object(),
        )


def test_assessment_agent_parses_pydantic_result() -> None:
    draft = make_draft()
    agent = AssessmentAgent(make_settings())

    result = agent._parse_result(FakeCrewResult(pydantic=draft))

    assert result == draft


def test_assessment_agent_parses_raw_json_result() -> None:
    draft = make_draft()
    agent = AssessmentAgent(make_settings())

    result = agent._parse_result(FakeCrewResult(raw=draft.model_dump_json()))

    assert result.title == "Evaluation RAG"
    assert len(result.questions) == 3


def test_assessment_agent_rejects_invalid_result() -> None:
    agent = AssessmentAgent(make_settings())

    with pytest.raises(AssessmentAgentOutputError):
        agent._parse_result(FakeCrewResult(raw='{"title": "bad"}'))


def test_assessment_agent_fallback_varies_questions_from_one_source() -> None:
    agent = AssessmentAgent(make_settings())

    draft = agent._fallback_draft(
        request=make_five_question_request(),
        source_map={"SOURCE_1": make_chunk()},
    )

    question_texts = [question.text for question in draft.questions]

    assert len(question_texts) == 5
    assert len(set(question_texts)) == 5


def test_assessment_agent_formats_gemini_model_for_crewai() -> None:
    agent = AssessmentAgent(make_settings())

    assert agent._gemini_model_name("gemini-2.0-flash") == "gemini/gemini-2.0-flash"
    assert agent._gemini_model_name("models/gemini-2.0-flash") == (
        "gemini/gemini-2.0-flash"
    )
    assert agent._gemini_model_name("gemini/gemini-2.0-flash") == (
        "gemini/gemini-2.0-flash"
    )


def test_assessment_agent_analyzes_weak_attempt_without_llm_call() -> None:
    agent = AssessmentAgent(make_settings(gemini_api_key=""))

    feedback = agent.analyze_attempt(
        score_percent=25,
        questions=[
            AssessmentCoachQuestionInput(
                question_id=1,
                question_text="Quel est le role de la convolution ?",
                expected_answer="Detecter des motifs dans une image.",
                explanation="La convolution applique un filtre.",
                points=1,
                points_awarded=0,
                evaluation_status="incorrect",
                feedback="Reponse incorrecte.",
                missing_concepts=["Detection de motifs"],
                source_document_id=10,
                source_document_title="CNN",
                source_page_number=7,
                source_excerpt="La convolution detecte des motifs avec un filtre.",
            )
        ],
    )

    assert feedback.mastery_level == "weak"
    assert feedback.points_a_renforcer == ["Detection de motifs"]
    assert feedback.points_acquis == []
    assert feedback.recommended_sources[0].document_id == 10
    assert feedback.recommended_sources[0].page_number == 7
    assert agent.last_state is not None
    assert agent.last_state.selected_task == "recommend_reinforcement"


def test_assessment_agent_analyzes_strong_attempt_as_acquired_points() -> None:
    agent = AssessmentAgent(make_settings(gemini_api_key=""))

    feedback = agent.analyze_attempt(
        score_percent=100,
        questions=[
            AssessmentCoachQuestionInput(
                question_id=1,
                question_text="Quel est le role du pooling ?",
                expected_answer="Reduire la dimension des cartes.",
                explanation="Le pooling simplifie les cartes.",
                points=1,
                points_awarded=1,
                evaluation_status="correct",
                feedback="Bonne reponse.",
                missing_concepts=[],
                source_document_id=10,
                source_document_title="CNN",
                source_page_number=9,
                source_excerpt="Le pooling reduit la taille des cartes.",
            )
        ],
    )

    assert feedback.mastery_level == "strong"
    assert feedback.points_a_renforcer == []
    assert feedback.points_acquis == ["Reduire la dimension des cartes."]
    assert feedback.recommended_sources[0].page_number == 9
    assert agent.last_state is not None
    assert agent.last_state.selected_task == "analyze_attempt"
