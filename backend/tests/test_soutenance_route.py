from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import get_soutenance_session_service
from app.models.user import User
from app.schemas.soutenance import (
    CreateSoutenanceSessionRequest,
    PublicSoutenanceQuestion,
    SoutenanceCurrentQuestionResponse,
    SoutenanceResultsResponse,
    SoutenanceRubricCriterionRead,
    SoutenanceSessionListResponse,
    SoutenanceSessionRead,
    SubmitSoutenanceAnswerRequest,
    SubmitSoutenanceAnswerResponse,
)
from app.services.soutenance import SoutenanceSessionCompletedError
from tests.test_auth import login_user, register_user


class FakeSoutenanceRouteService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def create_session(
        self,
        *,
        current_user: User,
        request: CreateSoutenanceSessionRequest,
    ) -> SoutenanceSessionRead:
        if self.error is not None:
            raise self.error
        return make_session()

    def list_sessions(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        status: str | None,
    ) -> SoutenanceSessionListResponse:
        return SoutenanceSessionListResponse(
            items=[],
            page=page,
            page_size=page_size,
            total=0,
            total_pages=0,
        )

    def get_session(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceSessionRead:
        return make_session(session_id=session_id)

    def get_current_question(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceCurrentQuestionResponse:
        return SoutenanceCurrentQuestionResponse(
            session_id=session_id,
            status="in_progress",
            mode="training",
            question_index=0,
            total_questions=3,
            progress_percentage=0,
            question=make_question(),
        )

    def submit_answer(
        self,
        *,
        current_user: User,
        session_id: int,
        request: SubmitSoutenanceAnswerRequest,
    ) -> SubmitSoutenanceAnswerResponse:
        if self.error is not None:
            raise self.error
        return SubmitSoutenanceAnswerResponse(
            session_id=session_id,
            question_id=request.question_id,
            mode="training",
            status="in_progress",
            feedback=make_feedback(),
            next_question=make_question(question_id=2),
            progress_percentage=33,
            message="Reponse evaluee.",
        )

    def complete_session(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceResultsResponse:
        return make_results(session_id)

    def get_results(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceResultsResponse:
        return make_results(session_id)

    def delete_session(self, *, current_user: User, session_id: int) -> None:
        return None


def make_question(question_id: int = 1) -> PublicSoutenanceQuestion:
    return PublicSoutenanceQuestion(
        id=question_id,
        text="Expliquez le role du Knowledge Agent.",
        category="ai_concepts",
        category_label="Concepts IA",
        difficulty="intermediate",
        order_index=0,
        answer_status="waiting",
    )


def make_feedback() -> dict[str, object]:
    return {
        "total_score": 80,
        "feedback": "Bonne reponse.",
        "strengths": ["Structure claire"],
        "missing_concepts": ["Ajouter les limites"],
        "improved_answer": "Reponse amelioree.",
        "recommendation": "Reviser la securite.",
        "rubric_scores": [
            SoutenanceRubricCriterionRead(
                criterion="technical_accuracy",
                label="Exactitude technique",
                weight=30,
                score=80,
                comment="Correct.",
            )
        ],
    }


def make_session(session_id: int = 1) -> SoutenanceSessionRead:
    return SoutenanceSessionRead(
        id=session_id,
        title="Simulation test",
        introduction="Preparation.",
        mode="training",
        difficulty="intermediate",
        status="in_progress",
        question_count=3,
        answered_count=0,
        current_question_index=0,
        progress_percentage=0,
        final_score=None,
        readiness_level=None,
        created_at="2026-07-26T00:00:00",
        completed_at=None,
        questions=[make_question()],
    )


def make_results(session_id: int) -> SoutenanceResultsResponse:
    return SoutenanceResultsResponse(
        id=session_id,
        title="Simulation test",
        mode="training",
        difficulty="intermediate",
        final_score=80,
        readiness_level="Bonne preparation",
        strengths=["Structure claire"],
        weaknesses=["Securite"],
        missing_concepts=["Limites"],
        recommendations=["Reviser la securite"],
        category_scores=[
            {
                "category": "ai_concepts",
                "category_label": "Concepts IA",
                "score": 80,
                "answered_count": 1,
            }
        ],
        questions=[
            {
                "question": make_question(),
                "answer_text": "Ma reponse.",
                "feedback": make_feedback(),
            }
        ],
        completed_at="2026-07-26T00:00:00",
    )


def auth_headers(client: TestClient) -> dict[str, str]:
    register_user(client, email="soutenance-route@example.com")
    login_payload = login_user(client, email="soutenance-route@example.com")
    return {"Authorization": f"Bearer {login_payload['access_token']}"}


def test_soutenance_sessions_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/soutenance-sessions")

    assert response.status_code == 401


def test_soutenance_route_creates_session(client: TestClient) -> None:
    client.app.dependency_overrides[get_soutenance_session_service] = lambda: (
        FakeSoutenanceRouteService()
    )

    response = client.post(
        "/api/v1/soutenance-sessions",
        headers=auth_headers(client),
        json={
            "mode": "training",
            "difficulty": "intermediate",
            "question_count": 3,
            "question_categories": ["architecture", "ai_concepts"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["questions"][0]["category"] == "ai_concepts"


def test_soutenance_route_submits_answer(client: TestClient) -> None:
    client.app.dependency_overrides[get_soutenance_session_service] = lambda: (
        FakeSoutenanceRouteService()
    )

    response = client.post(
        "/api/v1/soutenance-sessions/1/answers",
        headers=auth_headers(client),
        json={
            "question_id": 1,
            "answer": "J'explique le role de l'agent et ses limites.",
        },
    )

    assert response.status_code == 200
    assert response.json()["feedback"]["total_score"] == 80


def test_soutenance_route_maps_conflict(client: TestClient) -> None:
    client.app.dependency_overrides[get_soutenance_session_service] = lambda: (
        FakeSoutenanceRouteService(error=SoutenanceSessionCompletedError())
    )

    response = client.post(
        "/api/v1/soutenance-sessions/1/answers",
        headers=auth_headers(client),
        json={
            "question_id": 1,
            "answer": "J'explique le role de l'agent et ses limites.",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == SoutenanceSessionCompletedError.message


def test_soutenance_route_returns_results(client: TestClient) -> None:
    client.app.dependency_overrides[get_soutenance_session_service] = lambda: (
        FakeSoutenanceRouteService()
    )

    response = client.get(
        "/api/v1/soutenance-sessions/1/results",
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["readiness_level"] == "Bonne preparation"
