from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AssistantServiceDependency, CurrentUser
from app.schemas.assistant import AskQuestionRequest, AskQuestionResponse
from app.services.assistant import (
    AssistantConfigurationError,
    AssistantProviderError,
    SelectedDocumentsNotFoundError,
    SelectedDocumentsNotReadyError,
)

router = APIRouter(prefix="/assistant")


@router.post("/ask", response_model=AskQuestionResponse)
def ask_question(
    request: AskQuestionRequest,
    current_user: CurrentUser,
    assistant_service: AssistantServiceDependency,
) -> AskQuestionResponse:
    try:
        return assistant_service.ask_question(user=current_user, request=request)
    except SelectedDocumentsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except SelectedDocumentsNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except AssistantConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except AssistantProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
