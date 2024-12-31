from typing import Callable
from fastapi import Request
from utils.logger import logging
from fastapi.responses import JSONResponse


class FinanceTrackerApiError(Exception):
    """base error exception."""

    def __init__(self, detail: str = "Service is unavailable.", name: str = None) -> None:
        self.detail = detail
        self.name = name
        super().__init__(self.detail, self.name)


def create_exception_handler(
    status_code: int, detail_message: str
) -> Callable[[Request, FinanceTrackerApiError], JSONResponse]:
    detail = {"message": detail_message}

    async def exception_handler(_: Request, exc: FinanceTrackerApiError) -> JSONResponse:
        if exc:
            detail["message"] = exc.detail

        if exc.name:
            detail["message"] = f"{detail['message']} [{exc.name}]"

        logging.error(exc)
        return JSONResponse(status_code=status_code, content={"detail": detail["message"]})

    return exception_handler


class ServiceError(FinanceTrackerApiError):
    """failures in external API or Services, like DB or third-party services."""

    pass


class EntityAlreadyAddedError(FinanceTrackerApiError):
    """user trying input new data not null data."""

    pass


class EntityAlreadyVerifiedError(FinanceTrackerApiError):
    """user trying input new data into already verified data."""

    pass


class EntityForceInputSameDataError(FinanceTrackerApiError):
    """user trying input new data which same with old data."""

    pass


class EntityDoesNotExistError(FinanceTrackerApiError):
    """database returns nothing"""

    pass


class EntityAlreadyFilledError(FinanceTrackerApiError):
    """user try to input new data into not null data"""

    pass


class EntityDoesNotMatchedError(FinanceTrackerApiError):
    """user input data that not matched into saved record"""

    pass


class MandatoryInputError(FinanceTrackerApiError):
    """user should input data before proceeding to next endpoint"""

    pass


class DatabaseError(FinanceTrackerApiError):
    """exception for database query error"""

    pass


class EntityAlreadyExistError(FinanceTrackerApiError):
    """conflicted data, user trying to create something that already saved."""

    pass


class InvalidOperationError(FinanceTrackerApiError):
    """invalid operations like trying to delete a non-existing entity, etc."""

    pass


class AuthenticationFailed(FinanceTrackerApiError):
    """invalid authentication credentials"""

    pass


class InvalidTokenError(FinanceTrackerApiError):
    """invalid token"""

    pass
