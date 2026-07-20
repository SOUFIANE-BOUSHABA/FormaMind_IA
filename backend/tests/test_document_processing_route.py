from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_document_processing_service
from app.models.user import User
from app.schemas.rag import ProcessDocumentResponse
from app.services.document_processing import (
    DocumentNotProcessableError,
    DocumentProcessingError,
    NoUsableTextError,
)
from tests.test_auth import login_user, register_user


class FakeDocumentProcessingService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[int, int]] = []

    def process_document(
        self,
        *,
        user: User,
        document_id: int,
    ) -> ProcessDocumentResponse:
        self.calls.append((user.id, document_id))

        if self.error is not None:
            raise self.error

        return ProcessDocumentResponse(
            document_id=document_id,
            status="ready",
            page_count=3,
            chunk_count=8,
            message="Document analyse avec succes.",
        )


def auth_headers(client: TestClient) -> dict[str, str]:
    register_user(client, email="process-route@example.com")
    login_payload = login_user(client, email="process-route@example.com")
    return {"Authorization": f"Bearer {login_payload['access_token']}"}


def test_process_document_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/documents/10/process")

    assert response.status_code == 401


def test_process_document_returns_processing_result(client: TestClient) -> None:
    fake_service = FakeDocumentProcessingService()
    client.app.dependency_overrides[get_document_processing_service] = lambda: (
        fake_service
    )

    response = client.post(
        "/api/v1/documents/10/process",
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == 10
    assert payload["status"] == "ready"
    assert payload["chunk_count"] == 8
    assert fake_service.calls == [(1, 10)]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (NoUsableTextError(), 400),
        (DocumentNotProcessableError(), 409),
        (DocumentProcessingError(), 404),
    ],
)
def test_process_document_maps_service_errors(
    client: TestClient,
    error: Exception,
    expected_status: int,
) -> None:
    client.app.dependency_overrides[get_document_processing_service] = lambda: (
        FakeDocumentProcessingService(error=error)
    )

    response = client.post(
        "/api/v1/documents/10/process",
        headers=auth_headers(client),
    )

    assert response.status_code == expected_status
    assert response.json()["detail"]
