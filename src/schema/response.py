from typing import Optional, Any
from pydantic import BaseModel, field_validator, EmailStr
from src.schema.validator import UniqueIdValidator


class ResponseDefault(BaseModel):
    success: bool = True
    message: str = None
    data: Optional[Any] = None


class ResponseToken(BaseModel):
    access_token: str = None
    refresh_token: str = None
    token_type: str = "Bearer"


class UniqueId(BaseModel):
    unique_id: str = None

    @field_validator("unique_id")
    @classmethod
    def validate_pin(cls, unique_id: Optional[str]) -> str:
        return UniqueIdValidator.validate_uuid(unique_id=unique_id)


class ServerStatus(BaseModel):
    status: str = None

class FullName(BaseModel):
    full_name: str = None

class Email(BaseModel):
    email: EmailStr = None
    
class PhoneNumber(BaseModel):
    phone_number: str = None

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


class DetailEmailResponse(Email, IsEmailVerified):
    pass