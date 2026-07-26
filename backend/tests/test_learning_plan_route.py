from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import get_learning_plan_service
from app.models.user import User
from app.schemas.learning_plan import (
    GenerateLearningPlanRequest,
    LearningPlanListResponse,
    LearningPlanRead,
    UpdateLearningActivityStatusRequest,
)
from app.services.learning_plan import LearningPlanAlreadyExistsError
from tests.test_auth import login_user, register_user


class FakeLearningPlanService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def generate_plan(
        self,
        *,
        current_user: User,
        request: GenerateLearningPlanRequest,
    ) -> LearningPlanRead:
        if self.error is not None:
            raise self.error
        return make_plan(attempt_id=request.attempt_id)

    def list_plans(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        status: str | None,
    ) -> LearningPlanListResponse:
        return LearningPlanListResponse(
            items=[],
            page=page,
            page_size=page_size,
            total=0,
            total_pages=0,
        )

    def get_plan(self, *, current_user: User, plan_id: int) -> LearningPlanRead:
        return make_plan(plan_id=plan_id)

    def update_activity_status(
        self,
        *,
        current_user: User,
        plan_id: int,
        activity_id: int,
        request: UpdateLearningActivityStatusRequest,
    ) -> LearningPlanRead:
        return make_plan(plan_id=plan_id, activity_status=request.status)

    def delete_plan(self, *, current_user: User, plan_id: int) -> None:
        return None


def make_plan(
    *,
    plan_id: int = 1,
    attempt_id: int = 2,
    activity_status: str = "pending",
) -> LearningPlanRead:
    return LearningPlanRead(
        id=plan_id,
        attempt_id=attempt_id,
        assessment_title="Quiz CNN",
        title="Plan CNN",
        status="active",
        intensity="balanced",
        daily_minutes=45,
        start_date="2026-07-23",
        target_end_date="2026-07-23",
        progress_percentage=0,
        generated_summary="Summary",
        created_at="2026-07-23T00:00:00",
        updated_at="2026-07-23T00:00:00",
        modules=[
            {
                "id": 10,
                "title": "Module",
                "objective": "Objectif",
                "topic": "CNN",
                "priority": "high",
                "order_index": 0,
                "estimated_minutes": 30,
                "activities": [
                    {
                        "id": 20,
                        "title": "Activite",
                        "instructions": "Lire.",
                        "type": "review",
                        "status": activity_status,
                        "order_index": 0,
                        "scheduled_date": "2026-07-23",
                        "duration_minutes": 30,
                        "started_at": None,
                        "completed_at": None,
                        "sources": [
                            {
                                "document_id": 1,
                                "document_title": "Cours",
                                "page_number": 1,
                                "excerpt": "Source",
                            }
                        ],
                    }
                ],
            }
        ],
    )


def auth_headers(client: TestClient) -> dict[str, str]:
    register_user(client, email="learning-plan-route@example.com")
    login_payload = login_user(client, email="learning-plan-route@example.com")
    return {"Authorization": f"Bearer {login_payload['access_token']}"}


def test_learning_plans_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/learning-plans")

    assert response.status_code == 401


def test_learning_plan_route_generates_plan(client: TestClient) -> None:
    client.app.dependency_overrides[get_learning_plan_service] = lambda: (
        FakeLearningPlanService()
    )

    response = client.post(
        "/api/v1/learning-plans",
        headers=auth_headers(client),
        json={
            "attempt_id": 2,
            "daily_minutes": 45,
            "start_date": "2026-07-23",
            "intensity": "balanced",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["modules"][0]["activities"][0]["sources"][0]["document_id"] == 1


def test_learning_plan_route_maps_duplicate_active_plan(
    client: TestClient,
) -> None:
    client.app.dependency_overrides[get_learning_plan_service] = lambda: (
        FakeLearningPlanService(error=LearningPlanAlreadyExistsError())
    )

    response = client.post(
        "/api/v1/learning-plans",
        headers=auth_headers(client),
        json={
            "attempt_id": 2,
            "daily_minutes": 45,
            "start_date": "2026-07-23",
            "intensity": "balanced",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]
