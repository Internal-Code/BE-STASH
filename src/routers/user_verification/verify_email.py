from utils.query.general import find_record, update_record
from services.postgres.models import SendOtp, User
from typing import Annotated
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.validator import SecurityCodeValidator
from utils.helper import local_time
from src.schema.request_format import UserOtp
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user

# from utils.request_format import OTPVerification
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    InvalidOperationError,
)
# from utils.database.general import (
#     extract_data_otp,
#     update_verify_email_status,
# )

router = APIRouter(tags=["User Verification"], prefix="/user/verification")


async def verify_email_endpoint(
    schema: UserOtp, current_user: Annotated[dict, Depends(get_current_user)], db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    validated_otp = SecurityCodeValidator.validate_security_code(type="otp", value=schema.otp)
    otp_record = await find_record(db=db, table=SendOtp, unique_id=current_user.unique_id)

    try:
        if current_user.verified_email:
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_time > otp_record.blacklisted_at:
            raise InvalidOperationError(detail="OTP already expired.")

        if otp_record.otp_number != validated_otp:
            raise InvalidOperationError(detail="Invalid OTP code.")

        if current_time < otp_record.blacklisted_at and otp_record.otp_number == validated_otp:
            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": current_user.unique_id},
                data={"verified_email": True},
            )

            response.message = "Email successfully verified."

    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    endpoint=verify_email_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User email verification.",
)
