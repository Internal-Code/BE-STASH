from typing import Any, List, Dict, Union, Optional
from pydantic import BaseModel, Field
from services.postgre.attribute_type import UserRegistrationStateEnum


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


class UserRegisterStateResponse(BaseModel):
    status: UserRegistrationStateEnum = UserRegistrationStateEnum.pending
    steps: "UserRegisterStateStepsResponse" = Field(
        default_factory=lambda: UserRegisterStateStepsResponse()
    )


class UserRegisterStateStepsResponse(BaseModel):
    phone_number_verified: bool = False
    pin_created: bool = False
    user_id: Optional[int] = Field(default=None, ge=1)
    register_state_id: Optional[int] = Field(default=None, ge=1)
    pin_reset_id: Optional[int] = Field(default=None, ge=1)


class SendOtpMethodResponse(BaseModel):
    phone_number_verified: bool = False
    email_verified: bool = False
