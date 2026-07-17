from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db_session
from app.db.base import Base
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
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

    def override_db_session() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def register_user(
    client: TestClient,
    *,
    email: str = "rabie@example.com",
    password: str = "FormaMind123!",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Rabie",
            "password": password,
        },
    )
    assert response.status_code == 201
    return response.json()


def login_user(
    client: TestClient,
    *,
    email: str = "rabie@example.com",
    password: str = "FormaMind123!",
) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def test_register_user_success(client: TestClient) -> None:
    payload = register_user(client)

    assert payload["email"] == "rabie@example.com"
    assert payload["full_name"] == "Rabie"
    assert payload["is_active"] is True
    assert "hashed_password" not in payload


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    register_user(client, email="RABIE@example.com")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "rabie@example.com",
            "full_name": "Rabie Again",
            "password": "FormaMind123!",
        },
    )

    assert response.status_code == 409


def test_login_success(client: TestClient) -> None:
    register_user(client)

    payload = login_user(client)

    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "rabie@example.com"


def test_login_rejects_invalid_password(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "rabie@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client: TestClient) -> None:
    register_user(client)
    login_payload = login_user(client)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "rabie@example.com"


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
