class FinanceTrackerApiError(Exception):
    """base error exception."""

    def __init__(
        self, detail: str = "Service is unavailable.", name: str = None
    ) -> None:
        self.detail = detail
        self.name = name
        super().__init__(self.detail, self.name)


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
