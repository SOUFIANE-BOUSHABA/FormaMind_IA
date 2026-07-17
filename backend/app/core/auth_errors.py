class AuthenticationError(Exception):
    """Base class for authentication domain errors."""


class DuplicateEmailError(AuthenticationError):
    pass


class InvalidCredentialsError(AuthenticationError):
    pass


class InactiveUserError(AuthenticationError):
    pass


class InvalidAccessTokenError(AuthenticationError):
    pass
