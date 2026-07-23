from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import get_attempt_service
from app.models.user import User
from app.schemas.attempt import (
    AttemptDetailResponse,
    AttemptListResponse,
    AttemptQuestion,
    AttemptQuestionOption,
    AttemptResultsResponse,
    PublicAttemptAnswer,
    StartAttemptResponse,
)
from app.services.attempt import AttemptEvaluationError, AttemptNotFoundError
from tests.test_auth import login_user, register_user


class FakeAttemptService:
    def start_or_resume(
        self,
        *,
        current_user: User,
        assessment_id: int,
    ) -> StartAttemptResponse:
        return StartAttemptResponse(
            id=12,
            assessment_id=assessment_id,
            status="in_progress",
            started_at="2026-07-21T10:00:00",
            answered_count=0,
            total_questions=1,
        )

    def get_attempt(
        self,
        *,
        current_user: User,
        attempt_id: int,
    ) -> AttemptDetailResponse:
        if attempt_id == 404:
            raise AttemptNotFoundError
        return AttemptDetailResponse(
            id=attempt_id,
            assessment_id=5,
            assessment_title="Evaluation CNN",
            difficulty="intermediate",
            status="in_progress",
            started_at="2026-07-21T10:00:00",
            submitted_at=None,
            evaluated_at=None,
            answered_count=0,
            flagged_count=0,
            total_questions=1,
            questions=[
                AttemptQuestion(
                    id=100,
                    type="multiple_choice",
                    text="Question sans corrige expose",
                    points=1,
                    order_index=0,
                    options=[
                        AttemptQuestionOption(
                            id=1,
                            text="Option A",
                            order_index=0,
                        )
                    ],
                )
            ],
            answers=[],
        )

    def save_answer(
        self,
        *,
        current_user: User,
        attempt_id: int,
        question_id: int,
        request: object,
    ) -> PublicAttemptAnswer:
        return PublicAttemptAnswer(
            question_id=question_id,
            selected_option_id=1,
            text_answer=None,
            is_flagged=True,
        )

    def submit_attempt(
        self,
        *,
        current_user: User,
        attempt_id: int,
    ) -> AttemptResultsResponse:
        if attempt_id == 503:
            raise AttemptEvaluationError
        return make_results(attempt_id)

    def get_results(
        self,
        *,
        current_user: User,
        attempt_id: int,
    ) -> AttemptResultsResponse:
        return make_results(attempt_id)

    def list_attempts(
        self,
        *,
        current_user: User,
        assessment_id: int,
        page: int,
        page_size: int,
        status: str | None,
    ) -> AttemptListResponse:
        return AttemptListResponse(
            items=[],
            page=page,
            page_size=page_size,
            total=0,
            total_pages=0,
        )


def make_results(attempt_id: int) -> AttemptResultsResponse:
    return AttemptResultsResponse(
        id=attempt_id,
        assessment_id=5,
        assessment_title="Evaluation CNN",
        difficulty="intermediate",
        status="evaluated",
        score=1,
        max_score=1,
        percentage=100,
        level="Expert",
        strong_topics=["CNN"],
        weak_topics=[],
        started_at="2026-07-21T10:00:00",
        submitted_at="2026-07-21T10:05:00",
        evaluated_at="2026-07-21T10:05:00",
        questions=[],
    )


def auth_headers(client: TestClient) -> dict[str, str]:
    register_user(client, email="attempt-route@example.com")
    payload = login_user(client, email="attempt-route@example.com")
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_start_attempt_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/assessments/5/attempts")

    assert response.status_code == 401


def test_start_attempt_returns_attempt_summary(client: TestClient) -> None:
    client.app.dependency_overrides[get_attempt_service] = FakeAttemptService

    response = client.post(
        "/api/v1/assessments/5/attempts",
        headers=auth_headers(client),
    )

    assert response.status_code == 201
    assert response.json()["assessment_id"] == 5


def test_read_attempt_hides_correct_answers(client: TestClient) -> None:
    client.app.dependency_overrides[get_attempt_service] = FakeAttemptService

    response = client.get("/api/v1/attempts/12", headers=auth_headers(client))
    payload = response.json()

    assert response.status_code == 200
    assert "correct_answer" not in payload["questions"][0]
    assert "is_correct" not in payload["questions"][0]["options"][0]


def test_save_answer_returns_public_answer(client: TestClient) -> None:
    client.app.dependency_overrides[get_attempt_service] = FakeAttemptService

    response = client.put(
        "/api/v1/attempts/12/answers/100",
        headers=auth_headers(client),
        json={"selected_option_id": 1, "is_flagged": True},
    )

    assert response.status_code == 200
    assert response.json()["is_flagged"] is True


def test_submit_maps_evaluation_failure(client: TestClient) -> None:
    client.app.dependency_overrides[get_attempt_service] = FakeAttemptService

    response = client.post("/api/v1/attempts/503/submit", headers=auth_headers(client))

    assert response.status_code == 503


def test_results_return_evaluated_payload(client: TestClient) -> None:
    client.app.dependency_overrides[get_attempt_service] = FakeAttemptService

    response = client.get("/api/v1/attempts/12/results", headers=auth_headers(client))

    assert response.status_code == 200
    assert response.json()["percentage"] == 100
