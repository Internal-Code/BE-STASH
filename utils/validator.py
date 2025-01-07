from typing import Literal
from uuid import UUID
from sqlalchemy.engine.row import Row
from utils.custom_error import InvalidOperationError, EntityAlreadyExistError


def check_phone_number(phone_number: str) -> str:
    if not phone_number.isdigit():
        raise InvalidOperationError(detail="Phone number must contain only digits.")
    if not (10 <= len(phone_number) <= 13):
        raise InvalidOperationError(detail="Phone number must be between 10 or 13 digits long.")
    return phone_number


def check_security_code(value: str, type: Literal["otp", "pin"]) -> str:
    if not value.isdigit():
        raise InvalidOperationError(detail=f"{type.upper()} must contain only digits.")
    if len(value) != 6:
        raise InvalidOperationError(detail=f"{type.upper()} must be 6 digits long.")
    return value


def check_record(record: Row, column: str) -> None:
    if record:
        column_name = " ".join(column.split("_")).capitalize() if column.__contains__("_") else column.capitalize()
        raise EntityAlreadyExistError(detail=f"{column_name} already registered.")


def check_uuid(unique_id: str) -> str:
    try:
        valid_uuid = UUID(unique_id)
    except ValueError:
        raise InvalidOperationError(detail="Invalid unique id format.")
    return str(valid_uuid)
