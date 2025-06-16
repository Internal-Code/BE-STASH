from fastapi import status


class BaseError(Exception):
    def __init__(self, status_code: int, message: str, errors: dict):
        self.status_code = status_code
        self.message = message
        self.errors = errors


class ServiceError(BaseError):
    """Failure occured comes from internal / third party application"""

    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message=message,
            errors=errors,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class QueryError(BaseError):
    """Failure occured when invalid database query"""

    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message=message,
            errors=errors,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class NotFoundError(BaseError):
    """Failure occured when finding non-existing data"""

    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message=message, errors=errors, status_code=status.HTTP_404_NOT_FOUND
        )
