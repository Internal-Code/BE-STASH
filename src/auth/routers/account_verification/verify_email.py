# TODO: User should be in logged in state to verify email
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import OTPVerification
from fastapi import APIRouter, status

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_email_endpoint(
    schema: OTPVerification, unique_id: str
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
