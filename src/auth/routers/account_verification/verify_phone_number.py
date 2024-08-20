from pytz import timezone
from datetime import datetime
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.request_format import OTPVerification
from src.auth.utils.jwt.general import get_user
from fastapi import APIRouter, status, HTTPException
from src.auth.utils.database.general import (
    extract_phone_number_otp,
    update_phone_number_status,
    verify_uuid,
    check_otp,
)

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_phone_number_endpoint(
    schema: OTPVerification, unique_id: str
) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)

    try:
        initials_account = await extract_phone_number_otp(user_uuid=unique_id)
        now_utc = datetime.now(timezone("UTC"))

        if not initials_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="UUID data not found."
            )

        account = await get_user(unique_id=unique_id)

        if account.verified_phone_number:
            logging.info("User phone number already verified.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account phone number already verified.",
            )

        logging.info("User phone number not verified.")
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
            await update_phone_number_status(user_uuid=unique_id)

            response.success = True
            response.message = "Account phone number verified."
            response.data = UniqueID(unique_id=unique_id)

    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Exception error in verify_phone_number: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=verify_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="User phone number verification.",
)
