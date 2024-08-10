from fastapi import APIRouter, HTTPException, status
from src.auth.utils.logging import logging
from src.auth.utils.database.general import (
    is_using_registered_email,
    save_reset_password_id,
)
from src.auth.utils.request_format import UserForgotPassword
from src.auth.schema.response import ResponseDefault
from uuid_extensions import uuid7

router = APIRouter(tags=["users"], prefix="/users")


async def forgot_users(payload: UserForgotPassword) -> ResponseDefault:
    response = ResponseDefault()
    try:
        unique_id = str(uuid7())
        registered_user = await is_using_registered_email(email=payload.email)
        if not registered_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {payload.email} not found.",
            )
        await save_reset_password_id(email=payload.email, reset_id=unique_id)

        response.success = True
        response.message = f"User {payload.email} found."
        response.data = {"reset_id": unique_id}

    except HTTPException as e:
        logging.error(f"Error while forgot_users: {e}.")
        raise e
    return response


router.add_api_route(
    methods=["POST"],
    path="/forgot-password",
    response_model=ResponseDefault,
    endpoint=forgot_users,
    status_code=status.HTTP_200_OK,
    summary="Forgot users password",
)
