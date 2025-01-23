from pydantic import BaseModel
from typing import Optional, Any


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


class ServerStatus(BaseModel):
    status: Optional[str] = None


class IsEmailVerified(BaseModel):
    is_email_verified: bool = False


class IsPhoneNumberVerified(BaseModel):
    is_phone_number_verified: bool = False


class RegisterState(BaseModel):
    register_state: Optional[str] = None


class OTPState(BaseModel):
    otp_state: Optional[str] = None


class UserStatus(
    IsEmailVerified, IsPhoneNumberVerified, RegisterState, OTPState, UniqueId
):
    pass
