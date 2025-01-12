from uuid import UUID
from datetime import timedelta
from utils.helper import local_time
from utils.whatsapp_api import send_whatsapp
from fastapi import APIRouter, status, Depends, BackgroundTasks
from services.postgres.connection import get_db
from utils.generator import random_number
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import User, SendOtp
from src.schema.response import ResponseDefault, UniqueId
from utils.query.general import find_record, update_record
from src.schema.custom_state import RegisterAccountState
from src.schema.request_format import UserPhoneNumber
from utils.custom_error import (
    EntityForceInputSameDataError,
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    EntityAlreadyFilledError,
    InvalidOperationError,
)

router = APIRouter(tags=["User Wrong Account"], prefix="/user/wrong")


async def wrong_phone_number_endpoint(
    schema: UserPhoneNumber, unique_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    generated_otp = random_number(6)
    account_record = await find_record(db=db, table=User, unique_id=str(unique_id))
    registered_phone_number = await find_record(db=db, table=User, phone_number=schema.phone_number)
    otp_record = await find_record(db=db, table=SendOtp, unique_id=str(unique_id))
    try:
        if not account_record:
            raise DataNotFoundError(detail="Account not found.")

        if account_record.register_state == RegisterAccountState.SUCCESS:
            raise EntityAlreadyFilledError(detail="Account already set pin.")

        if account_record.phone_number == schema.phone_number:
            raise EntityForceInputSameDataError(detail="Cannot changed into same phone number.")

        if registered_phone_number:
            raise EntityAlreadyExistError(detail="Phone number already registered.")

        if current_time < otp_record.save_to_hit_at:
            raise InvalidOperationError(detail="Should wait in 1 minutes.")

        if current_time > otp_record.save_to_hit_at:
            background_tasks.add_task(
                send_whatsapp,
                message_template=(
                    "Your verification code is *{generated_otp}*. "
                    "Please enter this code to complete your verification. "
                    "Kindly note that this code will *expire in 3 minutes."
                ),
                phone_number=schema.phone_number,
                generated_otp=generated_otp,
            )

            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": str(unique_id)},
                data={"phone_number": schema.phone_number, "updated_at": current_time},
            )

            await update_record(
                db=db,
                table=SendOtp,
                conditions={"unique_id": str(unique_id)},
                data={
                    "updated_at": current_time,
                    "otp_number": generated_otp,
                    "current_api_hit": otp_record.current_api_hit + 1 if otp_record.current_api_hit else 1,
                    "save_to_hit_at": current_time + timedelta(minutes=1),
                    "blacklisted_at": current_time + timedelta(minutes=3),
                },
            )

            response.success = True
            response.message = "Sending OTP into updated phone number."
            response.data = UniqueId(unique_id=account_record.unique_id)

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number/{unique_id}",
    response_model=ResponseDefault,
    endpoint=wrong_phone_number_endpoint,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Wrong registered account phone number.",
)
