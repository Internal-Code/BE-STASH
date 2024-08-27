from pytz import timezone
from datetime import datetime
from fastapi import APIRouter, status
from src.auth.utils.logging import logging
from src.auth.utils.jwt.general import get_user
from src.auth.utils.validator import check_uuid, check_otp
from src.auth.utils.request_format import OTPVerification
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.routers.exceptions import (
    ServiceError,
    FinanceTrackerApiError,
    EntityAlreadyVerifiedError,
    EntityDoesNotExistError,
    InvalidOperationError,
)
from src.auth.utils.database.general import (
    extract_data_otp,
    update_phone_number_status,
)

router = APIRouter(tags=["account-verification"], prefix="/verify")


async def verify_phone_number_endpoint(
    schema: OTPVerification, unique_id: str
) -> ResponseDefault:
    response = ResponseDefault()
    await check_uuid(unique_id=unique_id)

    try:
        initials_account = await extract_data_otp(user_uuid=unique_id)
        now_utc = datetime.now(timezone("UTC"))

        if not initials_account:
            logging.info("OTP data not found.")
            raise EntityDoesNotExistError(detail="Data not found.")

        account = await get_user(unique_id=unique_id)

        if account.verified_phone_number:
            logging.info("User phone number already verified.")
            raise EntityAlreadyVerifiedError(
                detail="User phone number already verified."
            )

        logging.info("User phone number not verified.")
        await check_otp(otp=schema.otp)

        if now_utc > initials_account.blacklisted_at:
            raise InvalidOperationError(detail="OTP already expired.")

        if initials_account.otp_number != schema.otp:
            raise InvalidOperationError(detail="Invalid OTP code.")

        if (
            now_utc < initials_account.blacklisted_at
            and initials_account.otp_number == schema.otp
        ):
            await update_phone_number_status(user_uuid=unique_id)

            response.success = True
            response.message = "User phone number verified."
            response.data = UniqueID(unique_id=unique_id)

    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=verify_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User phone number verification.",
)
