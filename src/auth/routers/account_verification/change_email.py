# TODO user should in logged in state to change valid email
from typing import Annotated
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import OTPVerification
from src.auth.utils.jwt.general import get_current_user
from fastapi import APIRouter, status, Depends

router = APIRouter(tags=["account-verification"], prefix="/change")


async def change_email_endpoint(
    unique_id: str,
    schema: OTPVerification,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()

    try:
        pass
    except Exception:
        pass

    return response


router.add_api_route(
    methods=["POST"],
    path="/email/{unique_id}",
    endpoint=change_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send otp to user email.",
)
