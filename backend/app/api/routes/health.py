from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings
from app.core.config import Settings
from app.schemas.common import HealthResponse

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_app_settings)]


@router.get("/health", response_model=HealthResponse)
def health_check(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        environment=settings.app_env,
    )
