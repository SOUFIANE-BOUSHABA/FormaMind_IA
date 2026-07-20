from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.api.dependencies import (
    CurrentUser,
    DocumentProcessingServiceDependency,
    DocumentServiceDependency,
)
from app.schemas.documents import (
    DocumentListResponse,
    DocumentRead,
    DocumentSort,
    DocumentStatus,
    DocumentUploadResponse,
)
from app.schemas.rag import ProcessDocumentResponse
from app.services.document_processing import (
    DocumentNotProcessableError,
    DocumentProcessingError,
    NoUsableTextError,
)
from app.services.documents import (
    DocumentDeletionError,
    DocumentNotFoundError,
)
from app.storage.documents import DocumentStorageError

router = APIRouter(prefix="/documents")


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    document_service: DocumentServiceDependency,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
) -> DocumentUploadResponse:
    try:
        document = document_service.upload_document(
            user=current_user,
            file=file,
            title=title,
        )
    except DocumentStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    return DocumentUploadResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    document_service: DocumentServiceDependency,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 12,
    search: Annotated[str | None, Query(max_length=120)] = None,
    status_filter: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    sort: DocumentSort = "newest",
) -> DocumentListResponse:
    return document_service.list_documents(
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        sort=sort,
    )


@router.post("/{document_id}/process", response_model=ProcessDocumentResponse)
def process_document(
    document_id: int,
    current_user: CurrentUser,
    processing_service: DocumentProcessingServiceDependency,
) -> ProcessDocumentResponse:
    try:
        return processing_service.process_document(
            user=current_user,
            document_id=document_id,
        )
    except NoUsableTextError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    except DocumentNotProcessableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.get("/{document_id}", response_model=DocumentRead)
def read_document(
    document_id: int,
    document_service: DocumentServiceDependency,
    current_user: CurrentUser,
) -> DocumentRead:
    try:
        document = document_service.get_document(
            user=current_user,
            document_id=document_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc

    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    document_service: DocumentServiceDependency,
    current_user: CurrentUser,
) -> None:
    try:
        document_service.delete_document(user=current_user, document_id=document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except DocumentDeletionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        ) from exc
