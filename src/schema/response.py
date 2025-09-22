from typing import Any, List, Dict, Union
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """
    Base response model for API responses.
    """

    message: str = Field(
        default="Success",
        description="Human-readable message describing the result of the request",
    )
    data: Union[Dict[str, Any], List[Any]] = Field(
        default_factory=list,
        description="Response payload containing the data returned by the API",
    )


class TokenResponse(BaseModel):
    """
    Response model for authentication tokens.
    """

    access_token: str = Field(
        ..., description="JWT access token used for authenticated requests"
    )
    refresh_token: str = Field(
        ..., description="JWT refresh token used to obtain new access tokens"
    )
    token_type: str = Field(
        default="Bearer", description="Type of the token, typically 'Bearer'"
    )
