from typing import Annotated
from utils.logger import logging
from utils.jwt import JWTHandler
from utils.time_utils import local_time
from utils.query import QueryDatabase
from services.postgre.model import SendOtp, User
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from src.schema.request_format import Otp
from src.schema.response import ResponseDefault
from utils.error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    InvalidOperationError,
    MandatoryInputError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Verification"], prefix="/user/verification")


async def verify_email_endpoint(
    schema: Otp,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Verify email endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    current_time = local_time()
    otp_record = await query.find(table=SendOtp, unique_id=current_user.unique_id)

    try:
        if not current_user.email:
            logging.error("User is not add an email.")
            raise MandatoryInputError(detail="Should add email first.")

        if current_user.verified_email:
            logging.error("User email is not verified.")
            raise EntityAlreadyVerifiedError(detail="Email already verified.")

        if current_time > otp_record.blacklisted_at:
            logging.error("OTP expired.")
            raise InvalidOperationError(detail="OTP already expired.")

        if otp_record.otp_number != schema.otp:
            logging.error("Invalid OTP.")
            raise InvalidOperationError(detail="Invalid OTP code.")

        if (
            current_time < otp_record.blacklisted_at
            and otp_record.otp_number == schema.otp
        ):
            logging.info("Updating verify email state.")
            await query.update(
                table=User,
                condition={"unique_id": current_user.unique_id},
                data={"verified_email": True},
            )

            logging.info("Email verified.")
            response.message = "Email successfully verified."

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    endpoint=verify_email_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User email verification.",
)
