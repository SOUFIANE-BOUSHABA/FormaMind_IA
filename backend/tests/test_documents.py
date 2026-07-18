from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import fitz
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_document_service
from app.repositories.document import DocumentRepository
from app.services.documents import DocumentService
from app.storage.documents import DocumentStorageService
from tests.test_auth import login_user, register_user

db_session_dependency = Depends(get_db_session)


def make_pdf_bytes(page_count: int = 1) -> bytes:
    pdf = fitz.open()
    for _ in range(page_count):
        page = pdf.new_page()
        page.insert_text((72, 72), "FormaMind AI PDF")
    return pdf.tobytes()


@pytest.fixture
def document_client(
    client: TestClient,
    tmp_path: Path,
) -> tuple[TestClient, Path]:
    upload_root = tmp_path / "uploads" / "documents"

    def override_document_service(
        db: Session = db_session_dependency,
    ) -> DocumentService:
        return DocumentService(
            DocumentRepository(db),
            DocumentStorageService(
                upload_directory=upload_root,
                max_upload_size_mb=1,
            ),
        )

    client.app.dependency_overrides[get_document_service] = override_document_service
    return client, upload_root


def auth_headers(
    client: TestClient,
    *,
    email: str = "docs@example.com",
) -> dict[str, str]:
    register_user(client, email=email)
    login_payload = login_user(client, email=email)
    return {"Authorization": f"Bearer {login_payload['access_token']}"}


def upload_pdf(
    client: TestClient,
    *,
    headers: dict[str, str],
    filename: str = "support.pdf",
    title: str | None = "Support PDF",
    pages: int = 2,
) -> dict[str, Any]:
    files = {
        "file": (filename, BytesIO(make_pdf_bytes(pages)), "application/pdf"),
    }
    data = {"title": title} if title is not None else {}
    response = client.post(
        "/api/v1/documents",
        data=data,
        files=files,
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_upload_pdf_stores_metadata_and_file(
    document_client: tuple[TestClient, Path],
) -> None:
    client, upload_root = document_client
    headers = auth_headers(client)

    payload = upload_pdf(client, headers=headers, filename="cours-rag.pdf", pages=3)

    assert payload["title"] == "Support PDF"
    assert payload["original_filename"] == "cours-rag.pdf"
    assert payload["mime_type"] == "application/pdf"
    assert payload["page_count"] == 3
    assert payload["file_size"] > 0
    assert payload["status"] == "uploaded"
    assert "storage_key" not in payload
    assert len(list(upload_root.rglob("*.pdf"))) == 1


def test_upload_derives_title_from_filename(
    document_client: tuple[TestClient, Path],
) -> None:
    client, _upload_root = document_client
    headers = auth_headers(client)

    payload = upload_pdf(
        client,
        headers=headers,
        filename="architecture-cloud.pdf",
        title=None,
    )

    assert payload["title"] == "architecture-cloud"


def test_upload_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("support.pdf", BytesIO(make_pdf_bytes()), "application/pdf")},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("filename", "mime_type", "content"),
    [
        ("notes.txt", "text/plain", b"not a pdf"),
        ("notes.pdf", "text/plain", b"%PDF-1.7\n"),
        ("notes.pdf", "application/pdf", b"not a pdf"),
        ("empty.pdf", "application/pdf", b""),
    ],
)
def test_upload_rejects_invalid_files(
    document_client: tuple[TestClient, Path],
    filename: str,
    mime_type: str,
    content: bytes,
) -> None:
    client, upload_root = document_client
    email_slug = f"{Path(filename).stem}-{mime_type.replace('/', '-')}"
    headers = auth_headers(client, email=f"{email_slug}@example.com")

    response = client.post(
        "/api/v1/documents",
        files={"file": (filename, BytesIO(content), mime_type)},
        headers=headers,
    )

    assert response.status_code == 400
    assert list(upload_root.rglob("*.pdf")) == []


def test_upload_rejects_oversized_pdf(
    document_client: tuple[TestClient, Path],
) -> None:
    client, upload_root = document_client
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "large.pdf",
                BytesIO(b"%PDF-" + (b"0" * ((1024 * 1024) + 1))),
                "application/pdf",
            ),
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert list(upload_root.rglob("*.pdf")) == []


def test_list_documents_is_owner_scoped_and_searchable(
    document_client: tuple[TestClient, Path],
) -> None:
    client, _upload_root = document_client
    owner_headers = auth_headers(client, email="owner@example.com")
    other_headers = auth_headers(client, email="other@example.com")

    upload_pdf(client, headers=owner_headers, filename="rag.pdf", title="Cours RAG")
    upload_pdf(
        client,
        headers=owner_headers,
        filename="cloud.pdf",
        title="Architecture Cloud",
    )
    upload_pdf(client, headers=other_headers, filename="secret.pdf", title="Secret")

    response = client.get(
        "/api/v1/documents",
        params={"search": "cloud", "status": "uploaded", "page_size": 1},
        headers=owner_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["total_pages"] == 1
    assert payload["items"][0]["title"] == "Architecture Cloud"


def test_document_details_and_delete_are_owner_scoped(
    document_client: tuple[TestClient, Path],
) -> None:
    client, upload_root = document_client
    owner_headers = auth_headers(client, email="owner-details@example.com")
    other_headers = auth_headers(client, email="other-details@example.com")
    document = upload_pdf(client, headers=owner_headers)

    forbidden_detail = client.get(
        f"/api/v1/documents/{document['id']}",
        headers=other_headers,
    )
    forbidden_delete = client.delete(
        f"/api/v1/documents/{document['id']}",
        headers=other_headers,
    )
    owner_detail = client.get(
        f"/api/v1/documents/{document['id']}",
        headers=owner_headers,
    )
    owner_delete = client.delete(
        f"/api/v1/documents/{document['id']}",
        headers=owner_headers,
    )
    missing_detail = client.get(
        f"/api/v1/documents/{document['id']}",
        headers=owner_headers,
    )

    assert forbidden_detail.status_code == 404
    assert forbidden_delete.status_code == 404
    assert owner_detail.status_code == 200
    assert owner_detail.json()["id"] == document["id"]
    assert owner_delete.status_code == 204
    assert missing_detail.status_code == 404
    assert list(upload_root.rglob("*.pdf")) == []


def test_dashboard_document_count_uses_uploaded_documents(
    document_client: tuple[TestClient, Path],
) -> None:
    client, _upload_root = document_client
    headers = auth_headers(client, email="dashboard-docs@example.com")

    upload_pdf(client, headers=headers, filename="one.pdf")
    upload_pdf(client, headers=headers, filename="two.pdf")

    response = client.get("/api/v1/dashboard/summary", headers=headers)

    assert response.status_code == 200
    document_metric = next(
        metric
        for metric in response.json()["metrics"]
        if metric["label"] == "Documents"
    )
    assert document_metric["value"] == "2"
    assert document_metric["description"] == "PDF importés"
