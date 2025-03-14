from typing import Optional, Any
from pydantic import BaseModel, field_validator
from src.schema.validator import UniqueIdValidator


class ResponseDefault(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ResponseToken(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "Bearer"


class UniqueId(BaseModel):
    unique_id: Optional[str] = None

    @field_validator("unique_id")
    @classmethod
    def validate_pin(cls, unique_id: Optional[str]) -> str:
        return UniqueIdValidator.validate_uuid(unique_id=unique_id)


class MonthId(BaseModel):
    month_id: Optional[str] = None

    @field_validator("month_id")
    @classmethod
    def validate_month_id(cls, validate_month_id: Optional[str]) -> str:
        return UniqueIdValidator.validate_uuid(unique_id=validate_month_id)


class ServerStatus(BaseModel):
    status: Optional[str] = None


class IsEmailVerified(BaseModel):
    is_email_verified: bool = False


class IsPhoneNumberVerified(BaseModel):
    is_phone_number_verified: bool = False


class RegisterState(BaseModel):
    register_state: bool = False


class OTPState(BaseModel):
    otp_state: bool = False


class UserStatus(
    IsEmailVerified, IsPhoneNumberVerified, RegisterState, OTPState, UniqueId
):
    pass
