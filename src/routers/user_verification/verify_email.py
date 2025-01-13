from utils.query.general import find_record, update_record
from services.postgres.models import SendOtp, User
from typing import Annotated
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.helper import local_time
from src.schema.request_format import UserOtp
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    InvalidOperationError,
)


router = APIRouter(tags=["User Verification"], prefix="/user/verification")


async def verify_email_endpoint(
    schema: UserOtp, current_user: Annotated[dict, Depends(get_current_user)], db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    otp_record = await find_record(db=db, table=SendOtp, unique_id=current_user.unique_id)

    try:
        if current_user.verified_email:
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_time > otp_record.blacklisted_at:
            raise InvalidOperationError(detail="OTP already expired.")

        if otp_record.otp_number != schema.otp:
            raise InvalidOperationError(detail="Invalid OTP code.")

        if current_time < otp_record.blacklisted_at and otp_record.otp_number == schema.otp:
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
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    endpoint=verify_email_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User email verification.",
)
