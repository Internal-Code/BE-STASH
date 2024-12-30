from uuid import UUID
from uuid_extensions import uuid7
from utils.custom_error import InvalidOperationError


async def check_phone_number(phone_number: str) -> str:
    if not phone_number.isdigit():
        raise InvalidOperationError(detail="Phone number must contain only digits.")

    if not (10 <= len(phone_number) <= 13):
        raise InvalidOperationError(
            detail="Phone number must be between 10 or 13 digits long."
        )

    return phone_number


async def check_pin(pin: str) -> str:
    if not pin.isdigit():
        raise InvalidOperationError(detail="Pin number must contain only digits.")

    if len(pin) != 6:
        raise InvalidOperationError(detail="Pin number must be 6 digits long.")

    return pin


async def check_otp(otp: str) -> str:
    if not otp.isdigit():
        raise InvalidOperationError(detail="OTP number must contain only digits.")

    if len(otp) != 6:
        raise InvalidOperationError(detail="OTP number must be 6 digits long.")

    return otp


async def check_fullname(value: str) -> str:
    value = " ".join(value.split())

    if not all(char.isalpha() or char.isspace() for char in value):
        raise InvalidOperationError(
            detail="Fullname should contain only letters and spaces."
        )

    if len(value) > 100:
        raise InvalidOperationError(
            detail="Fullname should be less than 100 character."
        )

    fullname = value.title()

    return fullname


async def check_uuid(unique_id: uuid7) -> UUID:
    try:
        valid_uuid = UUID(unique_id)
    except ValueError:
        raise InvalidOperationError(detail="Invalid UUID format.")
    return valid_uuid
