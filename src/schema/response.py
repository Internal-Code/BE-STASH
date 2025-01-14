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


class UserStatus(UniqueId):
    register_status: Optional[str] = None
    verified_phone_number: bool = False
    verified_email: bool = False
