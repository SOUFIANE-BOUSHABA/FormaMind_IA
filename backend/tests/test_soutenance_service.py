from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.models.user import User
from app.repositories.soutenance import SoutenanceRepository
from app.schemas.soutenance import (
    RUBRIC_CRITERIA,
    CreateSoutenanceSessionRequest,
    SoutenanceAnswerEvaluationDraft,
    SoutenanceQuestionDraft,
    SoutenanceRubricScoreDraft,
    SoutenanceSessionDraft,
    SubmitSoutenanceAnswerRequest,
)
from app.services.soutenance import (
    SoutenanceCreationError,
    SoutenanceSessionService,
    WrongCurrentQuestionError,
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


class FakeSoutenanceCoachAgent:
    def __init__(self, duplicate_question: bool = False) -> None:
        self.duplicate_question = duplicate_question
        self.generated_calls = 0
        self.evaluated_calls = 0

    def generate_questions(self, **kwargs: object) -> SoutenanceSessionDraft:
        request = kwargs["request"]
        self.generated_calls += 1
        questions = []
        for index in range(request.question_count):
            text = (
                "Expliquez l'architecture globale de FormaMind AI."
                if self.duplicate_question
                else f"Question soutenance {index + 1} sur FormaMind AI ?"
            )
            questions.append(
                SoutenanceQuestionDraft(
                    local_id=f"q-{index + 1}",
                    text=text,
                    category=request.question_categories[
                        index % len(request.question_categories)
                    ],
                    difficulty=request.difficulty,
                    expected_concepts=["FastAPI", "React", "Agent"],
                    evaluation_focus="Verifier la justification technique.",
                    follow_up_hint="Demander une limite concrete.",
                    order_index=index,
                )
            )
        return SoutenanceSessionDraft(
            title="Simulation test",
            introduction="Preparation a la soutenance.",
            questions=questions,
        )

    def evaluate_answer(self, **kwargs: object) -> SoutenanceAnswerEvaluationDraft:
        question = kwargs["question"]
        self.evaluated_calls += 1
        return SoutenanceAnswerEvaluationDraft(
            question_id=question.id,
            total_score=82,
            feedback="Reponse claire avec des choix techniques justifies.",
            strengths=["Structure claire", "Bon lien avec le projet"],
            missing_concepts=["Ajouter les limites"],
            improved_answer="Je presenterais aussi les limites et les tests.",
            recommendation="Reviser les limites et la securite.",
            rubric_scores=[
                SoutenanceRubricScoreDraft(
                    criterion=criterion,
                    score=82,
                    comment=f"{criterion} maitrise.",
                )
                for criterion in RUBRIC_CRITERIA
            ],
        )


def create_user(db: Session) -> User:
    user = User(
        email="soutenance@example.com",
        full_name="Soutenance Learner",
        hashed_password="hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_service(
    db: Session,
    agent: FakeSoutenanceCoachAgent | None = None,
) -> SoutenanceSessionService:
    return SoutenanceSessionService(
        repository=SoutenanceRepository(db),
        soutenance_coach_agent=agent or FakeSoutenanceCoachAgent(),
        settings=Settings(_env_file=None),
    )


def make_request(mode: str = "training") -> CreateSoutenanceSessionRequest:
    return CreateSoutenanceSessionRequest(
        title="Demo soutenance",
        mode=mode,
        difficulty="intermediate",
        question_count=3,
        question_categories=["architecture", "ai_concepts", "technical"],
    )


def test_soutenance_service_creates_persisted_session(
    db_session: Session,
) -> None:
    user = create_user(db_session)
    agent = FakeSoutenanceCoachAgent()
    service = make_service(db_session, agent)

    session = service.create_session(current_user=user, request=make_request())

    assert agent.generated_calls == 1
    assert session.title == "Simulation test"
    assert session.status == "in_progress"
    assert session.question_count == 3
    assert [question.order_index for question in session.questions] == [0, 1, 2]


def test_soutenance_service_rejects_duplicate_questions(
    db_session: Session,
) -> None:
    user = create_user(db_session)
    service = make_service(db_session, FakeSoutenanceCoachAgent(True))

    with pytest.raises(SoutenanceCreationError):
        service.create_session(current_user=user, request=make_request())


def test_soutenance_service_submits_training_answer_with_feedback(
    db_session: Session,
) -> None:
    user = create_user(db_session)
    agent = FakeSoutenanceCoachAgent()
    service = make_service(db_session, agent)
    session = service.create_session(current_user=user, request=make_request())
    current = service.get_current_question(current_user=user, session_id=session.id)

    response = service.submit_answer(
        current_user=user,
        session_id=session.id,
        request=SubmitSoutenanceAnswerRequest(
            question_id=current.question.id,
            answer="Je presente l'architecture, les agents, FastAPI et React.",
        ),
    )

    assert agent.evaluated_calls == 1
    assert response.feedback is not None
    assert response.progress_percentage == 33
    assert response.next_question is not None


def test_soutenance_service_hides_feedback_in_jury_mode(
    db_session: Session,
) -> None:
    user = create_user(db_session)
    service = make_service(db_session)
    session = service.create_session(
        current_user=user,
        request=make_request(mode="jury"),
    )
    current = service.get_current_question(current_user=user, session_id=session.id)

    response = service.submit_answer(
        current_user=user,
        session_id=session.id,
        request=SubmitSoutenanceAnswerRequest(
            question_id=current.question.id,
            answer="Je justifie les choix, les limites et les tests du projet.",
        ),
    )

    assert response.feedback is None


def test_soutenance_service_blocks_wrong_or_duplicate_answer(
    db_session: Session,
) -> None:
    user = create_user(db_session)
    service = make_service(db_session)
    session = service.create_session(current_user=user, request=make_request())
    current = service.get_current_question(current_user=user, session_id=session.id)

    with pytest.raises(WrongCurrentQuestionError):
        service.submit_answer(
            current_user=user,
            session_id=session.id,
            request=SubmitSoutenanceAnswerRequest(
                question_id=current.question.id + 99,
                answer="Une reponse assez longue pour passer la validation.",
            ),
        )

    service.submit_answer(
        current_user=user,
        session_id=session.id,
        request=SubmitSoutenanceAnswerRequest(
            question_id=current.question.id,
            answer="Une reponse assez longue pour etre enregistree.",
        ),
    )

    with pytest.raises(WrongCurrentQuestionError):
        service.submit_answer(
            current_user=user,
            session_id=session.id,
            request=SubmitSoutenanceAnswerRequest(
                question_id=current.question.id,
                answer="Une deuxieme reponse sur une ancienne question.",
            ),
        )


def test_soutenance_service_completes_and_returns_results(
    db_session: Session,
) -> None:
    user = create_user(db_session)
    service = make_service(db_session)
    session = service.create_session(current_user=user, request=make_request())

    for _ in range(session.question_count):
        current = service.get_current_question(current_user=user, session_id=session.id)
        service.submit_answer(
            current_user=user,
            session_id=session.id,
            request=SubmitSoutenanceAnswerRequest(
                question_id=current.question.id,
                answer="Je reponds avec architecture, agents, securite et limites.",
            ),
        )

    results = service.get_results(current_user=user, session_id=session.id)

    assert results.final_score == 82
    assert results.readiness_level == "Bonne preparation"
    assert len(results.questions) == 3
    assert results.category_scores
