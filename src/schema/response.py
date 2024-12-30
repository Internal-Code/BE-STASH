from pydantic import BaseModel


class UniqueID(BaseModel):
    unique_id: str


class ResponseDefault(BaseModel):
    success: bool = False
    message: str = None
    data: list | dict | UniqueID = None


class ResponseToken(BaseModel):
    access_token: str = None
    refresh_token: str = None
    token_type: str = "Bearer"
