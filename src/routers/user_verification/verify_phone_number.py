from uuid import UUID
from utils.helper import local_time
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from services.postgres.models import SendOtp, User
from src.schema.response import ResponseDefault, UniqueId
from utils.query.general import find_record, update_record
from src.schema.validator import SecurityCodeValidator
from src.schema.request_format import UserOtp
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    EntityAlreadyVerifiedError,
    DataNotFoundError,
    InvalidOperationError,
)

router = APIRouter(tags=["User Verification"], prefix="/user/verification")


async def verify_phone_number_endpoint(
    schema: UserOtp, unique_id: UUID, db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    otp_record = await find_record(db=db, table=SendOtp, unique_id=str(unique_id))
    account_record = await find_record(db=db, table=User, unique_id=str(unique_id))
    current_time = local_time()
    validated_otp = SecurityCodeValidator.validate_security_code(type="otp", value=schema.otp)

    try:
        if not otp_record:
            raise DataNotFoundError(detail="Data not found.")

        if not otp_record.otp_number:
            raise DataNotFoundError(detail="OTP code not found. Please request a new OTP code.")

        if account_record.verified_phone_number:
            raise EntityAlreadyVerifiedError(detail="Phone number already verified.")

        if current_time > otp_record.blacklisted_at:
            raise InvalidOperationError(detail="OTP already expired.")

        if otp_record.otp_number != validated_otp:
            raise InvalidOperationError(detail="Invalid OTP code.")

        if current_time < otp_record.blacklisted_at and otp_record.otp_number == validated_otp:
            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": str(unique_id)},
                data={"verified_phone_number": True},
            )

            response.message = "Phone number successfully verified."
            response.data = UniqueId(unique_id=str(unique_id))

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number/{unique_id}",
    endpoint=verify_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User phone number verification.",
)
