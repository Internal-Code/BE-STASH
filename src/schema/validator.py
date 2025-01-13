from uuid import UUID
from typing import Literal
from utils.custom_error import InvalidOperationError


class FullNameValidatorMixin:
    @classmethod
    def validate_fullname(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise InvalidOperationError("Fullname should not be empty.")
        if not all(char.isalpha() or char.isspace() for char in value):
            raise InvalidOperationError("Fullname should contain only letters and space.")
        if len(value) >= 100:
            raise InvalidOperationError("Fullname should be less than 100 characters.")
        return value.title()


class PhoneNumberValidatorMixin:
    @classmethod
    def validate_phone_number(cls, phone_number: str) -> str:
        if not phone_number.isdigit():
            raise InvalidOperationError("Phone number must contain only digits.")
        if not (10 <= len(phone_number) <= 13):
            raise InvalidOperationError("Phone number must be between 10 to 13 digits long.")
        return phone_number


class SecurityCodeValidator:
    @classmethod
    def validate_security_code(cls, value: str, type: Literal["otp", "pin"]) -> str:
        if not value.isdigit():
            raise InvalidOperationError(detail=f"{type.upper()} must contain only digits.")
        if len(value) != 6:
            raise InvalidOperationError(detail=f"{type.upper()} must be 6 digits long.")
        return value


class UniqueIdValidator:
    @classmethod
    def validate_uuid(cls, unique_id: str) -> str:
        try:
            valid_uuid = UUID(unique_id)
        except ValueError:
            raise InvalidOperationError(detail="Invalid unique id format.")
        return str(valid_uuid)
