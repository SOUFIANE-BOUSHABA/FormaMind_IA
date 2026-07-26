from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import CurrentUser, LearningPlanServiceDependency
from app.schemas.learning_plan import (
    GenerateLearningPlanRequest,
    LearningPlanListResponse,
    LearningPlanRead,
    UpdateLearningActivityStatusRequest,
)
from app.services.learning_plan import (
    LearningActivityNotFoundError,
    LearningActivityTransitionError,
    LearningPlanAlreadyExistsError,
    LearningPlanAttemptNotFoundError,
    LearningPlanGenerationConfigurationError,
    LearningPlanGenerationInvalidOutputError,
    LearningPlanNotFoundError,
)

router = APIRouter(prefix="/learning-plans")


@router.post("", response_model=LearningPlanRead, status_code=status.HTTP_201_CREATED)
def generate_learning_plan(
    request: GenerateLearningPlanRequest,
    current_user: CurrentUser,
    learning_plan_service: LearningPlanServiceDependency,
) -> LearningPlanRead:
    try:
        return learning_plan_service.generate_plan(
            current_user=current_user,
            request=request,
        )
    except LearningPlanAttemptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except LearningPlanAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except LearningPlanGenerationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except LearningPlanGenerationInvalidOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc


@router.get("", response_model=LearningPlanListResponse)
def list_learning_plans(
    current_user: CurrentUser,
    learning_plan_service: LearningPlanServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> LearningPlanListResponse:
    return learning_plan_service.list_plans(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status_filter,
    )


@router.get("/{plan_id}", response_model=LearningPlanRead)
def read_learning_plan(
    plan_id: int,
    current_user: CurrentUser,
    learning_plan_service: LearningPlanServiceDependency,
) -> LearningPlanRead:
    try:
        return learning_plan_service.get_plan(
            current_user=current_user,
            plan_id=plan_id,
        )
    except LearningPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.patch("/{plan_id}/activities/{activity_id}", response_model=LearningPlanRead)
def update_learning_activity_status(
    plan_id: int,
    activity_id: int,
    request: UpdateLearningActivityStatusRequest,
    current_user: CurrentUser,
    learning_plan_service: LearningPlanServiceDependency,
) -> LearningPlanRead:
    try:
        return learning_plan_service.update_activity_status(
            current_user=current_user,
            plan_id=plan_id,
            activity_id=activity_id,
            request=request,
        )
    except (LearningPlanNotFoundError, LearningActivityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except LearningActivityTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learning_plan(
    plan_id: int,
    current_user: CurrentUser,
    learning_plan_service: LearningPlanServiceDependency,
) -> Response:
    try:
        learning_plan_service.delete_plan(
            current_user=current_user,
            plan_id=plan_id,
        )
    except LearningPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
