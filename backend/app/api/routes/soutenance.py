from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import CurrentUser, SoutenanceSessionServiceDependency
from app.schemas.soutenance import (
    CreateSoutenanceSessionRequest,
    SoutenanceCurrentQuestionResponse,
    SoutenanceResultsResponse,
    SoutenanceSessionListResponse,
    SoutenanceSessionRead,
    SubmitSoutenanceAnswerRequest,
    SubmitSoutenanceAnswerResponse,
)
from app.services.soutenance import (
    DuplicateSoutenanceAnswerError,
    SoutenanceCompletionError,
    SoutenanceConfigurationError,
    SoutenanceCreationError,
    SoutenanceEvaluationError,
    SoutenanceResultsUnavailableError,
    SoutenanceSessionCompletedError,
    SoutenanceSessionNotFoundError,
    WrongCurrentQuestionError,
)

router = APIRouter(prefix="/soutenance-sessions")


@router.post(
    "",
    response_model=SoutenanceSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_soutenance_session(
    request: CreateSoutenanceSessionRequest,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> SoutenanceSessionRead:
    try:
        return soutenance_service.create_session(
            current_user=current_user,
            request=request,
        )
    except SoutenanceConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except SoutenanceCreationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc


@router.get("", response_model=SoutenanceSessionListResponse)
def list_soutenance_sessions(
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> SoutenanceSessionListResponse:
    return soutenance_service.list_sessions(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status_filter,
    )


@router.get("/{session_id}", response_model=SoutenanceSessionRead)
def read_soutenance_session(
    session_id: int,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> SoutenanceSessionRead:
    try:
        return soutenance_service.get_session(
            current_user=current_user,
            session_id=session_id,
        )
    except SoutenanceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.get(
    "/{session_id}/current-question",
    response_model=SoutenanceCurrentQuestionResponse,
)
def read_current_soutenance_question(
    session_id: int,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> SoutenanceCurrentQuestionResponse:
    try:
        return soutenance_service.get_current_question(
            current_user=current_user,
            session_id=session_id,
        )
    except SoutenanceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post(
    "/{session_id}/answers",
    response_model=SubmitSoutenanceAnswerResponse,
)
def submit_soutenance_answer(
    session_id: int,
    request: SubmitSoutenanceAnswerRequest,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> SubmitSoutenanceAnswerResponse:
    try:
        return soutenance_service.submit_answer(
            current_user=current_user,
            session_id=session_id,
            request=request,
        )
    except SoutenanceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except (
        DuplicateSoutenanceAnswerError,
        SoutenanceSessionCompletedError,
        WrongCurrentQuestionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except SoutenanceEvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc


@router.post(
    "/{session_id}/complete",
    response_model=SoutenanceResultsResponse,
)
def complete_soutenance_session(
    session_id: int,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> SoutenanceResultsResponse:
    try:
        return soutenance_service.complete_session(
            current_user=current_user,
            session_id=session_id,
        )
    except SoutenanceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except SoutenanceCompletionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


@router.get("/{session_id}/results", response_model=SoutenanceResultsResponse)
def read_soutenance_results(
    session_id: int,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> SoutenanceResultsResponse:
    try:
        return soutenance_service.get_results(
            current_user=current_user,
            session_id=session_id,
        )
    except SoutenanceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except SoutenanceResultsUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_soutenance_session(
    session_id: int,
    current_user: CurrentUser,
    soutenance_service: SoutenanceSessionServiceDependency,
) -> Response:
    try:
        soutenance_service.delete_session(
            current_user=current_user,
            session_id=session_id,
        )
    except SoutenanceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
