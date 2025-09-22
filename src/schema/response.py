from typing import Any, List, Dict, Union
from pydantic import BaseModel


class BaseResponse(BaseModel):
    message: str
    data: Union[Dict[str, Any], List[Any]] = []


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
