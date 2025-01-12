from uuid import UUID
from utils.helper import local_time
from fastapi import APIRouter, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from services.postgres.models import SendOtp, User
from src.schema.response import ResponseDefault, UniqueId
from utils.query.general import find_record, update_record
from utils.whatsapp_api import send_whatsapp
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
    schema: UserOtp, unique_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    otp_record = await find_record(db=db, table=SendOtp, unique_id=str(unique_id))
    account_record = await find_record(db=db, table=User, unique_id=str(unique_id))
    current_time = local_time()

    try:
        if not otp_record:
            raise DataNotFoundError(detail="Data not found.")

        if not otp_record.otp_number:
            raise DataNotFoundError(detail="OTP code not found. Please request a new OTP code.")

        if account_record.verified_phone_number:
            raise EntityAlreadyVerifiedError(detail="Phone number already verified.")

        if current_time > otp_record.blacklisted_at:
            raise InvalidOperationError(detail="OTP already expired.")

        if otp_record.otp_number != schema.otp:
            raise InvalidOperationError(detail="Invalid OTP code.")

        if current_time < otp_record.blacklisted_at and otp_record.otp_number == schema.otp:
            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": str(unique_id)},
                data={"verified_phone_number": True},
            )

            background_tasks.add_task(
                send_whatsapp,
                message_template=(
                    "Dear *{full_name}*,\n\n"
                    "We are pleased to inform you that your phone number has been successfully verified.\n\n"
                    "You can now access all the features of your account with full verification.\n\n"
                    "If you did not request this verification or have any questions, please contact our support team.\n\n"
                    "Best regards,\n"
                    "*STASH Support Team*"
                ),
                full_name=account_record.full_name,
                phone_number=account_record.phone_number,
            )

            response.message = "Phone number successfully verified."
            response.data = UniqueId(unique_id=str(unique_id))

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number/{unique_id}",
    endpoint=verify_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="User phone number verification.",
)
