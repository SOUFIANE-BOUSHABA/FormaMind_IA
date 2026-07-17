from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthServiceDependency, CurrentUser
from app.core.auth_errors import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserPublic

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    auth_service: AuthServiceDependency,
) -> UserPublic:
    try:
        user = auth_service.register_user(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc

    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: UserLogin,
    auth_service: AuthServiceDependency,
) -> TokenResponse:
    try:
        user = auth_service.authenticate_user(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        ) from exc

    return TokenResponse(
        access_token=auth_service.create_login_token(user),
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic)
def read_current_user(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)
