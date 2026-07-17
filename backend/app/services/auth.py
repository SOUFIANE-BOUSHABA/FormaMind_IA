from __future__ import annotations

from app.core.auth_errors import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
)
from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserCreate, UserLogin


class AuthService:
    def __init__(self, users: UserRepository, settings: Settings) -> None:
        self.users = users
        self.settings = settings

    def register_user(self, data: UserCreate) -> User:
        if self.users.get_by_email(str(data.email)) is not None:
            raise DuplicateEmailError

        return self.users.create(
            email=str(data.email),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )

    def authenticate_user(self, data: UserLogin) -> User:
        user = self.users.get_by_email(str(data.email))
        if user is None or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveUserError

        return user

    def create_login_token(self, user: User) -> str:
        return create_access_token(user.id, self.settings)

    def get_user_from_token(self, token: str) -> User:
        try:
            user_id = decode_access_token(token, self.settings)
        except InvalidAccessTokenError:
            raise

        user = self.users.get_by_id(user_id)
        if user is None:
            raise InvalidAccessTokenError

        if not user.is_active:
            raise InactiveUserError

        return user
