from fastapi import status
from typing import Any


class BaseError(Exception):
    def __init__(self, status_code: int, message: str, error: dict[str, Any]):
        self.status_code = status_code
        self.message = message
        self.error = error


class QueryError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error=error,
        )


class NotFoundError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error=error,
        )


class AuthenticationError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error=error,
        )


class InvalidInputError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error=error,
        )


class ConflictDataError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error=error,
        )


class MandatoryInputError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error=error,
        )


class NotImplementedError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error=error,
        )


class ServiceError(BaseError):
    def __init__(self, message: str, error: dict[str, Any]):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error=error,
        )
