from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import AssessmentServiceDependency, CurrentUser
from app.schemas.assessment import (
    AssessmentListResponse,
    AssessmentRead,
    AssessmentSort,
    GenerateAssessmentRequest,
)
from app.services.assessment import (
    AssessmentDocumentsNotFoundError,
    AssessmentGenerationConfigurationError,
    AssessmentGenerationInvalidOutputError,
    AssessmentGenerationUnavailableError,
    AssessmentNotFoundError,
)

router = APIRouter(prefix="/assessments")


@router.post(
    "",
    response_model=AssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_assessment(
    request: GenerateAssessmentRequest,
    current_user: CurrentUser,
    assessment_service: AssessmentServiceDependency,
) -> AssessmentRead:
    try:
        return assessment_service.generate_assessment(
            current_user=current_user,
            request=request,
        )
    except AssessmentDocumentsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except AssessmentGenerationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except AssessmentGenerationInvalidOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc
    except AssessmentGenerationUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc


@router.get("", response_model=AssessmentListResponse)
def list_assessments(
    current_user: CurrentUser,
    assessment_service: AssessmentServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 12,
    sort: AssessmentSort = "newest",
) -> AssessmentListResponse:
    return assessment_service.list_assessments(
        current_user=current_user,
        page=page,
        page_size=page_size,
        sort=sort,
    )


@router.get("/{assessment_id}", response_model=AssessmentRead)
def read_assessment(
    assessment_id: int,
    current_user: CurrentUser,
    assessment_service: AssessmentServiceDependency,
) -> AssessmentRead:
    try:
        return assessment_service.get_assessment(
            current_user=current_user,
            assessment_id=assessment_id,
        )
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
