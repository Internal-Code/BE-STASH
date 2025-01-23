from typing import Callable
from fastapi import Request
from utils.logger import logging
from fastapi.responses import JSONResponse


class StashBaseApiError(Exception):
    """
    Base error exception.

    Attributes:
        - detail (str): A description of the error. Default is "Service is unavailable."
        - name (str, optional): An optional identifier for the error.
    """

    def __init__(
        self, detail: str = "Service is unavailable.", name: str = None
    ) -> None:
        self.detail = detail
        self.name = name
        super().__init__(self.detail, self.name)


def create_exception_handler(
    status_code: int, detail_message: str
) -> Callable[[Request, StashBaseApiError], JSONResponse]:
    """
    Create a custom exception handler for FastAPI.

    Args:
        - status_code (int): The HTTP status code to return with the response.
        - detail_message (str): The default error message if no custom error detail is provided.

    Returns:
        - Callable: An asynchronous function to handle the specified error.
    """
    detail = {"message": detail_message}

    async def exception_handler(_: Request, exc: StashBaseApiError) -> JSONResponse:
        if exc:
            detail["message"] = exc.detail

        if exc.name:
            detail["message"] = f"{detail['message']} [{exc.name}]"

        logging.error(exc)
        return JSONResponse(
            status_code=status_code, content={"detail": detail["message"]}
        )

    return exception_handler


class ServiceError(StashBaseApiError):
    """
    Failures in external API or services, such as database or third-party services.
    """


class DataNotFoundError(StashBaseApiError):
    """
    Raised when a query to the database or service returns no results.
    """


class EntityAlreadyVerifiedError(StashBaseApiError):
    """
    Raised when a user attempts to input new data into an already verified entity.
    """


class UserNotVerifiedError(StashBaseApiError):
    """
    Raised when a user attempts to perform an action requiring verification,
    but their account or data is not verified.
    """


class EntityForceInputSameDataError(StashBaseApiError):
    """
    Raised when a user tries to input new data that matches the previously saved data exactly.
    """


class EntityAlreadyFilledError(StashBaseApiError):
    """
    Raised when a user attempts to input data into a non-null field that already contains a value.
    """


class EntityDoesNotMatchedError(StashBaseApiError):
    """
    Raised when a user inputs data that does not match an existing saved record.
    """


class MandatoryInputError(StashBaseApiError):
    """
    Raised when a user does not provide required data to proceed to the next step or endpoint.
    """


class DatabaseQueryError(StashBaseApiError):
    """
    Raised when there is an error executing a database query.
    """


class EntityAlreadyExistError(StashBaseApiError):
    """
    Raised when a user attempts to create a resource or entity that already exists in the database.
    """


class InvalidOperationError(StashBaseApiError):
    """
    Raised for invalid operations, such as attempting to delete a non-existing entity or performing
    an unsupported action.
    """


class AuthenticationFailed(StashBaseApiError):
    """
    Raised when user authentication fails due to invalid credentials.
    """


class InvalidTokenError(StashBaseApiError):
    """
    Raised when a provided token is invalid or malformed.
    """
