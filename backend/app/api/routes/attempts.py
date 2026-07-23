from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import AttemptServiceDependency, CurrentUser
from app.schemas.attempt import (
    AttemptAnswerSaveRequest,
    AttemptDetailResponse,
    AttemptListResponse,
    AttemptResultsResponse,
    PublicAttemptAnswer,
    StartAttemptResponse,
)
from app.services.attempt import (
    AssessmentStartError,
    AttemptAlreadyEvaluatedError,
    AttemptEvaluationError,
    AttemptNotEvaluatedError,
    AttemptNotFoundError,
    InvalidAnswerError,
)

router = APIRouter()


@router.post(
    "/assessments/{assessment_id}/attempts",
    response_model=StartAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_assessment_attempt(
    assessment_id: int,
    current_user: CurrentUser,
    attempt_service: AttemptServiceDependency,
) -> StartAttemptResponse:
    try:
        return attempt_service.start_or_resume(
            current_user=current_user,
            assessment_id=assessment_id,
        )
    except AssessmentStartError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.get(
    "/assessments/{assessment_id}/attempts",
    response_model=AttemptListResponse,
)
def list_assessment_attempts(
    assessment_id: int,
    current_user: CurrentUser,
    attempt_service: AttemptServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> AttemptListResponse:
    try:
        return attempt_service.list_attempts(
            current_user=current_user,
            assessment_id=assessment_id,
            page=page,
            page_size=page_size,
            status=status_filter,
        )
    except AssessmentStartError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.get("/attempts/{attempt_id}", response_model=AttemptDetailResponse)
def read_attempt(
    attempt_id: int,
    current_user: CurrentUser,
    attempt_service: AttemptServiceDependency,
) -> AttemptDetailResponse:
    try:
        return attempt_service.get_attempt(
            current_user=current_user,
            attempt_id=attempt_id,
        )
    except AttemptNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.put(
    "/attempts/{attempt_id}/answers/{question_id}",
    response_model=PublicAttemptAnswer,
)
def save_attempt_answer(
    attempt_id: int,
    question_id: int,
    request: AttemptAnswerSaveRequest,
    current_user: CurrentUser,
    attempt_service: AttemptServiceDependency,
) -> PublicAttemptAnswer:
    try:
        return attempt_service.save_answer(
            current_user=current_user,
            attempt_id=attempt_id,
            question_id=question_id,
            request=request,
        )
    except AttemptNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except AttemptAlreadyEvaluatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except InvalidAnswerError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptResultsResponse)
def submit_attempt(
    attempt_id: int,
    current_user: CurrentUser,
    attempt_service: AttemptServiceDependency,
) -> AttemptResultsResponse:
    try:
        return attempt_service.submit_attempt(
            current_user=current_user,
            attempt_id=attempt_id,
        )
    except AttemptNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except AttemptAlreadyEvaluatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except AttemptEvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc


@router.get("/attempts/{attempt_id}/results", response_model=AttemptResultsResponse)
def read_attempt_results(
    attempt_id: int,
    current_user: CurrentUser,
    attempt_service: AttemptServiceDependency,
) -> AttemptResultsResponse:
    try:
        return attempt_service.get_results(
            current_user=current_user,
            attempt_id=attempt_id,
        )
    except AttemptNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except AttemptNotEvaluatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
