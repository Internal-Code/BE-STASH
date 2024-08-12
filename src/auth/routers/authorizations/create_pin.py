from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from src.auth.utils.jwt.general import get_current_user
from src.auth.utils.database.general import check_pin, save_user_pin
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import UserPin
from src.auth.utils.logging import logging

router = APIRouter(tags=["authorizations"], prefix="/auth")


async def create_pin(
    pin_data: UserPin,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    try:
        await check_pin(value=pin_data.pin)

        await save_user_pin(user_uuid=current_user.user_uuid, user_pin=pin_data.pin)
        logging.info(f"User {current_user.user_uuid} created a new PIN.")

        response.message = "PIN created successfully."
        response.success = True
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in create_pin: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/create-pin",
    response_model=ResponseDefault,
    endpoint=create_pin,
    summary="Create a new PIN.",
)
