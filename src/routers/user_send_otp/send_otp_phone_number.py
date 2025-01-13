from uuid import UUID
from datetime import timedelta
from src.secret import Config
from utils.logger import logging
from utils.helper import local_time
from services.postgres.models import SendOtp, User
from utils.generator import random_number
from utils.query.general import find_record, update_record
from fastapi import APIRouter, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.whatsapp_api import send_whatsapp
from src.schema.response import ResponseDefault, UniqueId
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    MandatoryInputError,
    InvalidOperationError,
)

config = Config()
router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_phone_number_endpoint(
    unique_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    generated_otp = random_number(6)
    otp_record = await find_record(db=db, table=SendOtp, unique_id=str(unique_id))
    account_record = await find_record(db=db, table=User, unique_id=str(unique_id))

    try:
        if not account_record:
            logging.info("OTP data initialization not found.")
            raise DataNotFoundError(detail="Data not found.")

        if not account_record.phone_number:
            logging.info("User should filled phone number yet.")
            raise MandatoryInputError(detail="User should fill phone number first.")

        if current_time < otp_record.save_to_hit_at:
            logging.info("User should wait API cooldown.")
            raise InvalidOperationError(detail="Should wait in 1 minutes.")

        if current_time > otp_record.save_to_hit_at:
            logging.info("Matched condition. Sending OTP using whatsapp API.")

            background_tasks.add_task(
                send_whatsapp,
                message_template=(
                    "Your verification code is *{generated_otp}*. "
                    "Please enter this code to complete your verification. "
                    "Kindly note that this code will *expire in 3 minutes*."
                ),
                phone_number=account_record.phone_number,
                generated_otp=generated_otp,
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

            response.message = f"OTP sent to {account_record.phone_number}."
            response.data = UniqueId(unique_id=str(unique_id))
    except StashBaseApiError:
        raise
    except Exception as e:
        raise ServiceError(detail=f"Service error: {e}.", name="STASH")
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=send_otp_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="Send otp phone number.",
)
