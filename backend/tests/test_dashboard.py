from __future__ import annotations

from fastapi.testclient import TestClient

from tests.test_auth import login_user, register_user


def test_dashboard_summary_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 401


def test_dashboard_summary_returns_authenticated_user_summary(
    client: TestClient,
) -> None:
    register_user(client, email="dashboard@example.com")
    login_payload = login_user(client, email="dashboard@example.com")

    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["learner_name"] == "Rabie"
    assert payload["greeting"] == "Bonjour Rabie,"
    assert len(payload["metrics"]) == 6
    assert payload["metrics"][0]["label"] == "Score global"
    assert payload["skills"][2]["label"] == "NLP"
    assert payload["agents"][1]["status"] == "active"
