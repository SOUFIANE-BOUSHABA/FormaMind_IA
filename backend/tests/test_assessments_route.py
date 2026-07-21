from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import get_assessment_service
from app.models.user import User
from app.schemas.assessment import (
    AssessmentListResponse,
    AssessmentRead,
    GenerateAssessmentRequest,
    PublicAssessmentDocument,
    PublicQuestion,
    PublicQuestionOption,
)
from app.services.assessment import (
    AssessmentDocumentsNotFoundError,
    AssessmentGenerationConfigurationError,
    AssessmentGenerationInvalidOutputError,
    AssessmentGenerationUnavailableError,
    AssessmentNotFoundError,
)
from tests.test_auth import login_user, register_user


def make_assessment_read(assessment_id: int = 10) -> AssessmentRead:
    return AssessmentRead(
        id=assessment_id,
        title="Evaluation RAG",
        difficulty="intermediate",
        status="generated",
        question_count=1,
        created_at="2026-07-20T10:00:00",
        updated_at="2026-07-20T10:00:00",
        documents=[
            PublicAssessmentDocument(
                id=1,
                title="Cours RAG",
                page_count=4,
            )
        ],
        questions=[
            PublicQuestion(
                id=100,
                type="multiple_choice",
                text="Quel est le role du RAG ?",
                points=1,
                order_index=0,
                source_document_id=1,
                source_document_title="Cours RAG",
                source_page_number=1,
                source_excerpt="Le RAG combine recherche et generation.",
                options=[
                    PublicQuestionOption(
                        id=1,
                        text="Chercher du contexte",
                        order_index=0,
                    ),
                    PublicQuestionOption(id=2, text="Compiler du code", order_index=1),
                ],
            )
        ],
    )


class FakeAssessmentService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.generated_requests: list[tuple[int, GenerateAssessmentRequest]] = []

    def generate_assessment(
        self,
        *,
        current_user: User,
        request: GenerateAssessmentRequest,
    ) -> AssessmentRead:
        self.generated_requests.append((current_user.id, request))
        if self.error is not None:
            raise self.error
        return make_assessment_read()

    def list_assessments(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        sort: str,
    ) -> AssessmentListResponse:
        return AssessmentListResponse(
            items=[],
            page=page,
            page_size=page_size,
            total=0,
            total_pages=0,
        )

    def get_assessment(
        self,
        *,
        current_user: User,
        assessment_id: int,
    ) -> AssessmentRead:
        if self.error is not None:
            raise self.error
        return make_assessment_read(assessment_id)


def auth_headers(client: TestClient) -> dict[str, str]:
    register_user(client, email="assessments-route@example.com")
    login_payload = login_user(client, email="assessments-route@example.com")
    return {"Authorization": f"Bearer {login_payload['access_token']}"}


def test_generate_assessment_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/assessments", json={})

    assert response.status_code == 401


def test_generate_assessment_returns_created_assessment(client: TestClient) -> None:
    fake_service = FakeAssessmentService()
    client.app.dependency_overrides[get_assessment_service] = lambda: fake_service

    response = client.post(
        "/api/v1/assessments",
        headers=auth_headers(client),
        json={
            "document_ids": [1],
            "topics": ["RAG"],
            "difficulty": "intermediate",
            "question_count": 3,
            "question_types": ["multiple_choice"],
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Evaluation RAG"
    assert fake_service.generated_requests[0][0] == 1


def test_list_assessments_returns_page(client: TestClient) -> None:
    client.app.dependency_overrides[get_assessment_service] = lambda: (
        FakeAssessmentService()
    )

    response = client.get(
        "/api/v1/assessments",
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_assessment_returns_detail(client: TestClient) -> None:
    client.app.dependency_overrides[get_assessment_service] = lambda: (
        FakeAssessmentService()
    )

    response = client.get(
        "/api/v1/assessments/42",
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["id"] == 42


def test_read_assessment_maps_not_found(client: TestClient) -> None:
    client.app.dependency_overrides[get_assessment_service] = lambda: (
        FakeAssessmentService(error=AssessmentNotFoundError())
    )

    response = client.get(
        "/api/v1/assessments/42",
        headers=auth_headers(client),
    )

    assert response.status_code == 404


def test_generate_assessment_maps_service_errors(client: TestClient) -> None:
    error_cases = [
        (AssessmentDocumentsNotFoundError(), 409),
        (AssessmentGenerationConfigurationError(), 503),
        (AssessmentGenerationInvalidOutputError(), 502),
        (AssessmentGenerationUnavailableError(), 503),
    ]

    for index, (error, expected_status) in enumerate(error_cases):
        client.app.dependency_overrides[get_assessment_service] = lambda error=error: (
            FakeAssessmentService(error=error)
        )

        register_user(client, email=f"assessment-error-{index}@example.com")
        login_payload = login_user(
            client,
            email=f"assessment-error-{index}@example.com",
        )
        response = client.post(
            "/api/v1/assessments",
            headers={"Authorization": f"Bearer {login_payload['access_token']}"},
            json={
                "document_ids": [1],
                "topics": ["RAG"],
                "difficulty": "intermediate",
                "question_count": 3,
                "question_types": ["multiple_choice"],
            },
        )

        assert response.status_code == expected_status
