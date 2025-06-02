from uuid import UUID
from typing import Literal
from utils.error import InvalidOperationError


class Validator:
    def __init__(self):
        pass

    def phone_number(self, phone_number: str) -> str:
        if not phone_number:
            raise InvalidOperationError("Phone number should not be empty.")
        if not phone_number.isdigit():
            raise InvalidOperationError("Phone number must contain only digits.")
        if not (10 <= len(phone_number) <= 20):
            raise InvalidOperationError(
                "Phone number must be between 10 to 20 digits long."
            )
        return phone_number

    def name(self, name: str, field: Literal["first_name", "last_name"]) -> str:
        name = " ".join(name.split())
        if not name:
            raise InvalidOperationError(f"{field} should not be empty.")
        if not all(char.isalpha() for char in name):
            raise InvalidOperationError(f"{field} should contain only letters.")
        if len(name) >= 20:
            raise InvalidOperationError(f"{field} should be less than 20 characters.")
        return name.title()


class FullNameValidatorMixin:
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise InvalidOperationError("Fullname should not be empty.")
        if not all(char.isalpha() for char in value):
            raise InvalidOperationError(
                "Fullname should contain only letters and space."
            )
        if len(value) >= 100:
            raise InvalidOperationError("Fullname should be less than 100 characters.")
        return value.title()


class PhoneNumberValidatorMixin:
    @classmethod
    def validate_phone_number(cls, phone_number: str) -> str:
        if not phone_number:
            raise InvalidOperationError("Phone number should not be empty")
        if not phone_number.isdigit():
            raise InvalidOperationError("Phone number must contain only digits.")
        if not (10 <= len(phone_number) <= 13):
            raise InvalidOperationError(
                "Phone number must be between 10 to 13 digits long."
            )
        return phone_number


class SecurityCodeValidator:
    @classmethod
    def validate_security_code(cls, value: str, type: Literal["otp", "pin"]) -> str:
        if not value:
            raise InvalidOperationError(f"{type.upper()} should not be empty.")

        if not value.isdigit():
            raise InvalidOperationError(
                detail=f"{type.upper()} must contain only digits."
            )
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


class YearValidator:
    @classmethod
    def year_must_be_four_digits(cls, value: int) -> int:
        if len(str(value)) != 4:
            raise ValueError("Year should be exactly 4 digits long")
        return value
