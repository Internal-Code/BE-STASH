from fastapi import status, FastAPI
from utils.custom_error import create_exception_handler
from utils.custom_error import (
    AuthenticationFailed,
    EntityAlreadyExistError,
    EntityDoesNotExistError,
    EntityAlreadyVerifiedError,
    ServiceError,
    InvalidOperationError,
    InvalidTokenError,
    EntityAlreadyAddedError,
    EntityForceInputSameDataError,
    DatabaseError,
    EntityDoesNotMatchedError,
    MandatoryInputError,
    EntityAlreadyFilledError,
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        exc_class_or_status_code=InvalidOperationError,
        handler=create_exception_handler(status.HTTP_400_BAD_REQUEST, "Can't perform the operation."),
    )

    app.add_exception_handler(
        exc_class_or_status_code=AuthenticationFailed,
        handler=create_exception_handler(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication failed due to invalid credentials.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityDoesNotExistError,
        handler=create_exception_handler(status.HTTP_404_NOT_FOUND, "Entity does not exist."),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityAlreadyFilledError,
        handler=create_exception_handler(status.HTTP_403_FORBIDDEN, "Entity already filled."),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityDoesNotMatchedError,
        handler=create_exception_handler(
            status.HTTP_400_BAD_REQUEST,
            "User input data that does not matched on saved data on database.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityAlreadyExistError,
        handler=create_exception_handler(
            status.HTTP_409_CONFLICT,
            "Entity already saved.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityAlreadyVerifiedError,
        handler=create_exception_handler(
            status.HTTP_403_FORBIDDEN,
            "Entity already verified.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityForceInputSameDataError,
        handler=create_exception_handler(
            status.HTTP_403_FORBIDDEN,
            "Cannot use same data.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityAlreadyAddedError,
        handler=create_exception_handler(
            status.HTTP_403_FORBIDDEN,
            "Entity already have data.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=InvalidTokenError,
        handler=create_exception_handler(status.HTTP_401_UNAUTHORIZED, "Invalid token, please re-authenticate again."),
    )

    app.add_exception_handler(
        exc_class_or_status_code=ServiceError,
        handler=create_exception_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "A service seems to be down, try again later.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=DatabaseError,
        handler=create_exception_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database error.",
        ),
    )

    app.add_exception_handler(
        exc_class_or_status_code=MandatoryInputError,
        handler=create_exception_handler(
            status.HTTP_403_FORBIDDEN,
            "User not inputed mandatory data yet.",
        ),
    )
