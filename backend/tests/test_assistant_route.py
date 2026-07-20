from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_assistant_service
from app.models.user import User
from app.schemas.assistant import (
    AskQuestionRequest,
    AskQuestionResponse,
    SourceCitation,
)
from app.services.assistant import (
    AssistantConfigurationError,
    AssistantProviderError,
    SelectedDocumentsNotFoundError,
    SelectedDocumentsNotReadyError,
)
from tests.test_auth import login_user, register_user


class FakeAssistantService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[int, AskQuestionRequest]] = []

    def ask_question(
        self,
        *,
        user: User,
        request: AskQuestionRequest,
    ) -> AskQuestionResponse:
        self.calls.append((user.id, request))

        if self.error is not None:
            raise self.error

        return AskQuestionResponse(
            answer="Le RAG combine recherche et generation.",
            has_sufficient_context=True,
            sources=[
                SourceCitation(
                    document_id=request.document_ids[0],
                    document_title="Cours RAG",
                    page_number=2,
                    excerpt="Le RAG combine recherche et generation.",
                )
            ],
        )


def auth_headers(client: TestClient) -> dict[str, str]:
    register_user(client, email="assistant-route@example.com")
    login_payload = login_user(client, email="assistant-route@example.com")
    return {"Authorization": f"Bearer {login_payload['access_token']}"}


def test_assistant_ask_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/assistant/ask",
        json={"document_ids": [1], "question": "C'est quoi le RAG ?"},
    )

    assert response.status_code == 401


def test_assistant_ask_returns_structured_answer(client: TestClient) -> None:
    fake_service = FakeAssistantService()
    client.app.dependency_overrides[get_assistant_service] = lambda: fake_service

    response = client.post(
        "/api/v1/assistant/ask",
        headers=auth_headers(client),
        json={"document_ids": [1], "question": "C'est quoi le RAG ?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Le RAG combine recherche et generation."
    assert payload["has_sufficient_context"] is True
    assert payload["sources"][0]["document_id"] == 1
    assert payload["sources"][0]["page_number"] == 2
    assert fake_service.calls[0][1].question == "C'est quoi le RAG ?"


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (SelectedDocumentsNotFoundError(), 404),
        (SelectedDocumentsNotReadyError(), 409),
        (AssistantConfigurationError(), 503),
        (AssistantProviderError(), 503),
    ],
)
def test_assistant_ask_maps_service_errors(
    client: TestClient,
    error: Exception,
    expected_status: int,
) -> None:
    client.app.dependency_overrides[get_assistant_service] = lambda: (
        FakeAssistantService(error=error)
    )

    response = client.post(
        "/api/v1/assistant/ask",
        headers=auth_headers(client),
        json={"document_ids": [1], "question": "C'est quoi le RAG ?"},
    )

    assert response.status_code == expected_status
    assert response.json()["detail"]
