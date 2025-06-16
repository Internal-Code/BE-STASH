from typing import Union
from pydantic import BaseModel


class ResponseDefault(BaseModel):
    success: bool = True
    message: str = None
    data: Union[dict, list] = None


class ResponseToken(BaseModel):
    access_token: str = None
    refresh_token: str = None
    token_type: str = "Bearer"
