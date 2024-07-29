from pydantic import BaseModel


class ResponseDefault(BaseModel):
    success: bool = False
    message: str = None
    data: dict | list = None


class ResponseToken(BaseModel):
    access_token: str = None
    refresh_token: str = None
    token_type: str = "Bearer"
