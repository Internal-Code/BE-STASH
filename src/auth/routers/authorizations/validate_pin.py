from src.auth.utils.logging import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from src.auth.utils.jwt.general import get_current_user
from src.auth.utils.database.general import verify_user_pin
from src.auth.utils.request_format import UserPin
from src.auth.schema.response import ResponseDefault

router = APIRouter(tags=["authorizations"], prefix="/auth")


async def validate_pin(
    pin_data: UserPin,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    try:
        if not current_user.pin_enabled:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PIN feature is not enabled.",
            )

        valid_pin = await verify_user_pin(
            user_uuid=current_user.user_uuid, pin=pin_data.pin
        )

        if not valid_pin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN.",
            )

        response.message = "PIN verified."
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in validate_pin: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/validate-pin",
    response_model=ResponseDefault,
    endpoint=validate_pin,
    summary="Verify user PIN.",
)
