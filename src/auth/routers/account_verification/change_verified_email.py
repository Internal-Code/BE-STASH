from typing import Annotated
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import AddEmail
from src.auth.utils.jwt.general import get_current_user
from fastapi import APIRouter, status, Depends, HTTPException
from src.auth.utils.database.general import (
    is_using_registered_email,
    update_user_email,
    extract_data_otp,
    save_otp_data,
    local_time,
    update_otp_data,
)

router = APIRouter(tags=["account-verification"], prefix="/change")


async def change_email_verified_endpoint(
    schema: AddEmail,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    registered_email = await is_using_registered_email(email=schema.email)
    initial_data = await extract_data_otp(user_uuid=current_user.user_uuid)

    try:
        if not current_user.verified_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User email should be verified first.",
            )

        if current_user.email == schema.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot use same email."
            )

        if registered_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already taken. Please use another email.",
            )

        await update_user_email(
            user_uuid=current_user.user_uuid, email=schema.email, verified_email=False
        )

        if initial_data.current_api_hit != 1:
            logging.info("Re-initialized OTP save data.")
            await update_otp_data(user_uuid=current_user.user_uuid)

        if not initial_data:
            logging.info("Initialized OTP save data.")
            await save_otp_data(
                user_uuid=current_user.user_uuid,
                current_api_hit=1,
                saved_by_system=True,
                save_to_hit_at=local_time(),
            )

        response.success = True
        response.message = "Success update user email."

    except HTTPException as E:
        raise E

    except Exception as E:
        logging.error(f"Error while change verified email: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/verified-email",
    endpoint=change_email_verified_endpoint,
    status_code=status.HTTP_200_OK,
    response_model=ResponseDefault,
    summary="Change user email.",
)
