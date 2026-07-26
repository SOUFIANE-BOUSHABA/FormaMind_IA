from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    AssessmentDocument,
    Question,
    QuestionOption,
    StudentAnswer,
)
from app.models.document import Document
from app.models.user import User
from app.repositories.learning_plan import LearningPlanRepository
from app.schemas.learning_plan import (
    GenerateLearningPlanRequest,
    LearningActivityDraft,
    LearningModuleDraft,
    LearningPlanDraft,
    UpdateLearningActivityStatusRequest,
)
from app.schemas.rag import RetrievedChunk
from app.services.learning_plan import (
    LearningActivityTransitionError,
    LearningPlanService,
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


class FakeRetrieverTool:
    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                vector_id=f"document-{document_ids[0]}-page-1-chunk-0",
                user_id=user_id,
                document_id=document_ids[0],
                document_title="Cours CNN",
                page_number=1,
                chunk_index=0,
                text=f"Source fiable pour {question}.",
                relevance_score=0.91,
            )
        ]


class FakeLearningCoachAgent:
    def generate_plan(self, **kwargs: object) -> LearningPlanDraft:
        content_tool = kwargs["learning_content_tool"]
        content_tool._run(
            topic="convolution",
            missing_concepts=["filtres"],
            target_difficulty="intermediate",
            desired_learning_objective="renforcer la notion",
        )
        return LearningPlanDraft(
            title="Plan CNN",
            generated_summary="Plan personnalise pour renforcer la convolution.",
            modules=[
                LearningModuleDraft(
                    title="Consolider la convolution",
                    objective="Comprendre le role des filtres.",
                    topic="convolution",
                    priority="high",
                    activities=[
                        LearningActivityDraft(
                            title="Relire la source",
                            instructions="Lire, noter, puis reformuler.",
                            type="review",
                            duration_minutes=25,
                            source_refs=["CONTENT_SOURCE_1"],
                        )
                    ],
                )
            ],
        )


def create_evaluated_attempt(db: Session) -> tuple[User, AssessmentAttempt]:
    user = User(
        email="coach@example.com",
        full_name="Coach Learner",
        hashed_password="hash",
    )
    document = Document(
        user=user,
        title="Cours CNN",
        original_filename="cnn.pdf",
        stored_filename="cnn.pdf",
        storage_key="u/cnn.pdf",
        mime_type="application/pdf",
        file_size=100,
        page_count=3,
        status="ready",
    )
    assessment = Assessment(
        user=user,
        title="Quiz CNN",
        difficulty="intermediate",
        question_count=1,
    )
    assessment.documents.append(AssessmentDocument(document=document))
    question = Question(
        assessment=assessment,
        type="multiple_choice",
        text="Quel est le role d'un filtre ?",
        correct_answer="Detecter un motif",
        explanation="Le filtre detecte des motifs.",
        points=1,
        order_index=0,
        source_document=document,
        source_page_number=1,
        source_excerpt="Le filtre detecte des motifs.",
    )
    option = QuestionOption(
        question=question,
        text="Detecter un motif",
        is_correct=True,
        order_index=0,
    )
    attempt = AssessmentAttempt(
        assessment=assessment,
        user=user,
        status="evaluated",
        score=0,
        max_score=1,
        percentage=0,
        level="A renforcer",
        weak_topics=["Cours CNN"],
    )
    answer = StudentAnswer(
        attempt=attempt,
        question=question,
        selected_option=option,
        evaluation_status="incorrect",
        is_correct=False,
        points_awarded=0,
        feedback="Revoir le role du filtre.",
        missing_concepts=["filtres"],
    )
    db.add_all([user, document, assessment, question, option, attempt, answer])
    db.commit()
    return user, attempt


def make_service(db: Session) -> LearningPlanService:
    return LearningPlanService(
        repository=LearningPlanRepository(db),
        learning_coach_agent=FakeLearningCoachAgent(),
        retriever_tool=FakeRetrieverTool(),
    )


def test_learning_plan_service_generates_and_persists_plan(
    db_session: Session,
) -> None:
    user, attempt = create_evaluated_attempt(db_session)
    service = make_service(db_session)

    plan = service.generate_plan(
        current_user=user,
        request=GenerateLearningPlanRequest(
            attempt_id=attempt.id,
            daily_minutes=45,
            start_date="2026-07-23",
            intensity="balanced",
        ),
    )

    assert plan.title == "Plan CNN"
    assert plan.assessment_title == "Quiz CNN"
    assert plan.modules[0].activities[0].scheduled_date == "2026-07-23"
    assert plan.modules[0].activities[0].sources[0].document_title == "Cours CNN"


def test_learning_plan_service_returns_existing_active_plan(
    db_session: Session,
) -> None:
    user, attempt = create_evaluated_attempt(db_session)
    service = make_service(db_session)
    request = GenerateLearningPlanRequest(
        attempt_id=attempt.id,
        daily_minutes=45,
        start_date="2026-07-23",
        intensity="balanced",
    )

    first_plan = service.generate_plan(current_user=user, request=request)

    second_plan = service.generate_plan(current_user=user, request=request)

    assert second_plan.id == first_plan.id


def test_learning_plan_service_updates_progress(
    db_session: Session,
) -> None:
    user, attempt = create_evaluated_attempt(db_session)
    service = make_service(db_session)
    plan = service.generate_plan(
        current_user=user,
        request=GenerateLearningPlanRequest(
            attempt_id=attempt.id,
            daily_minutes=45,
            start_date="2026-07-23",
            intensity="balanced",
        ),
    )
    activity_id = plan.modules[0].activities[0].id

    with pytest.raises(LearningActivityTransitionError):
        service.update_activity_status(
            current_user=user,
            plan_id=plan.id,
            activity_id=activity_id,
            request=UpdateLearningActivityStatusRequest(status="completed"),
        )

    plan = service.update_activity_status(
        current_user=user,
        plan_id=plan.id,
        activity_id=activity_id,
        request=UpdateLearningActivityStatusRequest(status="in_progress"),
    )
    assert plan.modules[0].activities[0].status == "in_progress"

    plan = service.update_activity_status(
        current_user=user,
        plan_id=plan.id,
        activity_id=activity_id,
        request=UpdateLearningActivityStatusRequest(status="completed"),
    )
    assert plan.progress_percentage == 100
    assert plan.status == "completed"
