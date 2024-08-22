# TODO: user should be in logged in state to verify valid email
from typing import Annotated
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import OTPVerification
from src.auth.utils.jwt.general import verify_email_status
from fastapi import APIRouter, status, Depends

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_email_endpoint(
    schema: OTPVerification,
    email_status: Annotated[dict, Depends(verify_email_status)],
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
    endpoint=verify_email_endpoint,
    status_code=status.HTTP_200_OK,
    summary="User email verification.",
)
