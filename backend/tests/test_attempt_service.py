from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.assessment import (
    Assessment,
    AssessmentDocument,
    Question,
    QuestionOption,
)
from app.models.document import Document
from app.models.user import User
from app.repositories.attempt import AttemptRepository
from app.schemas.attempt import (
    AssessmentCoachFeedback,
    AssessmentCoachQuestionInput,
    AssessmentCoachSource,
    AttemptAnswerSaveRequest,
    OpenAnswerEvaluation,
)
from app.services.attempt import (
    AttemptAlreadyEvaluatedError,
    AttemptEvaluationError,
    AttemptService,
    InvalidAnswerError,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class FakeAssessmentAgent:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0
        self.analysis_calls: list[tuple[float, list[AssessmentCoachQuestionInput]]] = []

    def evaluate_open_answers(self, inputs: list) -> list[OpenAnswerEvaluation]:
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider unavailable")

        return [
            OpenAnswerEvaluation(
                question_id=item.question_id,
                points_awarded=item.max_points / 2,
                evaluation_status="partial",
                feedback="Reponse partielle mais pertinente.",
                missing_concepts=["precision"],
            )
            for item in inputs
        ]

    def analyze_attempt(
        self,
        *,
        score_percent: float,
        questions: list[AssessmentCoachQuestionInput],
    ) -> AssessmentCoachFeedback:
        self.analysis_calls.append((score_percent, questions))
        weak_questions = [
            question
            for question in questions
            if question.evaluation_status in {"incorrect", "partial", "unanswered"}
        ]
        return AssessmentCoachFeedback(
            score_percent=score_percent,
            mastery_level="weak" if score_percent < 55 else "strong",
            summary="Feedback pedagogique de test.",
            points_a_renforcer=[
                question.expected_answer for question in weak_questions
            ],
            points_acquis=[
                question.expected_answer
                for question in questions
                if question.evaluation_status == "correct"
            ],
            recommended_actions=["Relire les pages recommandees."],
            recommended_sources=[
                AssessmentCoachSource(
                    document_id=question.source_document_id,
                    document_title=question.source_document_title,
                    page_number=question.source_page_number,
                    excerpt=question.source_excerpt,
                    reason="Question a renforcer.",
                )
                for question in weak_questions[:3]
            ],
            confidence="high",
        )


def make_user(email: str = "learner@example.com") -> User:
    return User(email=email, full_name="Learner", hashed_password="hash")


def make_document(user: User) -> Document:
    return Document(
        user=user,
        title="CNN",
        original_filename="cnn.pdf",
        stored_filename="cnn.pdf",
        storage_key="1/cnn.pdf",
        mime_type="application/pdf",
        file_size=100,
        page_count=3,
        status="ready",
    )


def make_assessment(user: User, document: Document) -> Assessment:
    assessment = Assessment(
        user=user,
        title="Evaluation CNN",
        difficulty="intermediate",
        status="generated",
        question_count=3,
    )
    assessment.documents.append(AssessmentDocument(document=document))
    qcm = Question(
        assessment=assessment,
        type="multiple_choice",
        text="Quel est le role d'une couche dense ?",
        correct_answer="Relier les neurones",
        explanation="La couche dense connecte les neurones.",
        points=1,
        order_index=0,
        source_document=document,
        source_page_number=1,
        source_excerpt="Une couche dense relie les neurones.",
    )
    qcm.options.extend(
        [
            QuestionOption(text="Relier les neurones", is_correct=True, order_index=0),
            QuestionOption(
                text="Supprimer les donnees",
                is_correct=False,
                order_index=1,
            ),
        ]
    )
    true_false = Question(
        assessment=assessment,
        type="true_false",
        text="La convolution peut extraire des caracteristiques.",
        correct_answer="Vrai",
        explanation="La convolution detecte des motifs.",
        points=1,
        order_index=1,
        source_document=document,
        source_page_number=2,
        source_excerpt="La convolution extrait des caracteristiques.",
    )
    true_false.options.extend(
        [
            QuestionOption(text="Vrai", is_correct=True, order_index=0),
            QuestionOption(text="Faux", is_correct=False, order_index=1),
        ]
    )
    short = Question(
        assessment=assessment,
        type="short_answer",
        text="Expliquez le pooling.",
        correct_answer="Le pooling reduit la dimension.",
        explanation="Credit partiel si la reduction est mentionnee.",
        points=2,
        order_index=2,
        source_document=document,
        source_page_number=3,
        source_excerpt="Le pooling reduit la taille des cartes.",
    )
    assessment.questions.extend([qcm, true_false, short])
    return assessment


def make_service(
    db_session: Session,
    *,
    agent: FakeAssessmentAgent | None = None,
) -> AttemptService:
    return AttemptService(
        repository=AttemptRepository(db_session),
        assessment_agent=agent or FakeAssessmentAgent(),
    )


def persist_assessment(db_session: Session) -> tuple[User, Assessment]:
    user = make_user()
    document = make_document(user)
    assessment = make_assessment(user, document)
    db_session.add(user)
    db_session.add(document)
    db_session.add(assessment)
    db_session.commit()
    return user, assessment


def test_start_twice_resumes_same_in_progress_attempt(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session)

    first = service.start_or_resume(current_user=user, assessment_id=assessment.id)
    second = service.start_or_resume(current_user=user, assessment_id=assessment.id)

    assert first.id == second.id
    assert second.total_questions == 3


def test_attempt_detail_hides_answer_keys(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session)
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)

    detail = service.get_attempt(current_user=user, attempt_id=attempt.id)

    assert detail.questions[0].options[0].text == "Relier les neurones"
    assert not hasattr(detail.questions[0].options[0], "is_correct")
    assert not hasattr(detail.questions[0], "correct_answer")


def test_save_answer_upserts_and_persists_flag(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session)
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)
    question = assessment.questions[0]

    service.save_answer(
        current_user=user,
        attempt_id=attempt.id,
        question_id=question.id,
        request=AttemptAnswerSaveRequest(
            selected_option_id=question.options[1].id,
            is_flagged=True,
        ),
    )
    service.save_answer(
        current_user=user,
        attempt_id=attempt.id,
        question_id=question.id,
        request=AttemptAnswerSaveRequest(
            selected_option_id=question.options[0].id,
            is_flagged=False,
        ),
    )
    detail = service.get_attempt(current_user=user, attempt_id=attempt.id)

    assert len(detail.answers) == 1
    assert detail.answers[0].selected_option_id == question.options[0].id
    assert detail.answers[0].is_flagged is False


def test_invalid_option_is_rejected(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session)
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)

    with pytest.raises(InvalidAnswerError):
        service.save_answer(
            current_user=user,
            attempt_id=attempt.id,
            question_id=assessment.questions[0].id,
            request=AttemptAnswerSaveRequest(selected_option_id=999),
        )


def test_flag_can_persist_without_selected_option(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session)
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)

    saved = service.save_answer(
        current_user=user,
        attempt_id=attempt.id,
        question_id=assessment.questions[0].id,
        request=AttemptAnswerSaveRequest(is_flagged=True),
    )

    assert saved.selected_option_id is None
    assert saved.is_flagged is True


def test_submit_grades_objective_and_open_answers(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    agent = FakeAssessmentAgent()
    service = make_service(db_session, agent=agent)
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)

    service.save_answer(
        current_user=user,
        attempt_id=attempt.id,
        question_id=assessment.questions[0].id,
        request=AttemptAnswerSaveRequest(
            selected_option_id=assessment.questions[0].options[0].id,
        ),
    )
    service.save_answer(
        current_user=user,
        attempt_id=attempt.id,
        question_id=assessment.questions[2].id,
        request=AttemptAnswerSaveRequest(text_answer="Le pooling reduit la taille."),
    )

    results = service.submit_attempt(current_user=user, attempt_id=attempt.id)

    assert results.status == "evaluated"
    assert results.score == 2.0
    assert results.max_score == 4.0
    assert results.percentage == 50.0
    assert agent.calls == 1
    assert len(agent.analysis_calls) == 1
    assert results.coach_feedback is not None
    assert results.coach_feedback.mastery_level == "weak"
    assert "Vrai" in results.coach_feedback.points_a_renforcer
    assert results.coach_feedback.recommended_sources[0].document_id == document_id(
        assessment,
    )
    assert results.questions[0].learner_answer.evaluation_status == "correct"
    assert results.questions[1].learner_answer.evaluation_status == "unanswered"
    assert results.questions[2].learner_answer.evaluation_status == "partial"


def document_id(assessment: Assessment) -> int:
    return assessment.questions[0].source_document_id


def test_evaluated_attempt_cannot_be_edited(db_session: Session) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session)
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)
    service.submit_attempt(current_user=user, attempt_id=attempt.id)

    with pytest.raises(AttemptAlreadyEvaluatedError):
        service.save_answer(
            current_user=user,
            attempt_id=attempt.id,
            question_id=assessment.questions[0].id,
            request=AttemptAnswerSaveRequest(
                selected_option_id=assessment.questions[0].options[0].id,
            ),
        )


def test_agent_failure_restores_in_progress_and_keeps_answers(
    db_session: Session,
) -> None:
    user, assessment = persist_assessment(db_session)
    service = make_service(db_session, agent=FakeAssessmentAgent(fail=True))
    attempt = service.start_or_resume(current_user=user, assessment_id=assessment.id)
    service.save_answer(
        current_user=user,
        attempt_id=attempt.id,
        question_id=assessment.questions[2].id,
        request=AttemptAnswerSaveRequest(text_answer="Une reponse courte."),
    )

    with pytest.raises(AttemptEvaluationError):
        service.submit_attempt(current_user=user, attempt_id=attempt.id)

    detail = service.get_attempt(current_user=user, attempt_id=attempt.id)
    assert detail.status == "in_progress"
    assert detail.answers[0].text_answer == "Une reponse courte."
    assert detail.answers[0].evaluation_status is None
