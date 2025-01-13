from pydantic import BaseModel
from typing import Optional, Any


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


class UserStatus(UniqueId):
    register_status: str = None
