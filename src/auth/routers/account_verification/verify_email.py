from pytz import timezone
from datetime import datetime
from typing import Annotated
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import OTPVerification
from src.auth.utils.jwt.general import get_current_user
from fastapi import APIRouter, status, Depends, HTTPException
from src.auth.utils.database.general import (
    extract_data_otp,
    check_otp,
    update_verify_email_status,
)

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_email_endpoint(
    schema: OTPVerification,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()

    try:
        initials_account = await extract_data_otp(user_uuid=current_user.user_uuid)
        now_utc = datetime.now(timezone("UTC"))

        if not initials_account:
            logging.info("OTP data not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Data not found."
            )

        if not current_user.email:
            logging.info("User is not input email yet.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User should add email first.",
            )

        if current_user.verified_email:
            logging.info("User email already verified.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User email already verified.",
            )

        await check_otp(otp=schema.otp)

        if now_utc > initials_account.blacklisted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP already expired.",
            )

        if initials_account.otp_number != schema.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code."
            )

        if (
            now_utc < initials_account.blacklisted_at
            and initials_account.otp_number == schema.otp
        ):
            await update_verify_email_status(user_uuid=current_user.user_uuid)

            response.success = True
            response.message = "User email verified."

    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in verify_email_endpoint: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )

    return response


router.add_api_route(
    methods=["POST"],
    path="/email",
    endpoint=verify_email_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User email verification.",
)
