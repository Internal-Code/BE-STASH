from uuid import UUID
from datetime import timedelta
from src.secret import Config
from utils.logger import logging
from utils.helper import local_time
from utils.query import QueryDatabase
from utils.generator import Generator
from utils.whatsapp_api import send_whatsapp
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import SendOtp, User
from fastapi import APIRouter, status, Depends, BackgroundTasks
from src.schema.response import ResponseDefault, UniqueId
from utils.error import (
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
    InvalidOperationError,
    DataNotFoundError,
)

config = Config()
router = APIRouter(tags=["User Send OTP"], prefix="/user/send-otp")


async def send_otp_phone_number_endpoint(
    unique_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Send OTP phone number endpoint.")
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)
    current_time = local_time()
    unique_id = str(unique_id)
    generated_otp = generator.random_number(6)
    account_record = await query.find(table=User, unique_id=unique_id)

    try:
        otp_record = await query.find(table=SendOtp, unique_id=unique_id)

        if not otp_record:
            logging.error("OTP record not found")
            raise DataNotFoundError("OTP record not found.")

        remaining_time = otp_record.save_to_hit_at.second - current_time.second

        if not account_record:
            logging.info("OTP data initialization not found.")
            raise DataNotFoundError(detail="Data not found.")

        if not account_record.phone_number:
            logging.info("User is not add phone number.")
            raise MandatoryInputError(detail="User should fill phone number first.")

        if current_time < otp_record.save_to_hit_at:
            logging.info(f"Should wait for API cooldown {remaining_time}s.")
            raise InvalidOperationError(detail=f"Should wait in {remaining_time}s.")

        if current_time > otp_record.save_to_hit_at:
            logging.info("Sending send otp into phone number.")
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
            await query.update(
                table=SendOtp,
                condition={"unique_id": unique_id},
                data={
                    "updated_at": current_time,
                    "otp_number": generated_otp,
                    "current_api_hit": otp_record.current_api_hit + 1
                    if otp_record.current_api_hit
                    else 1,
                    "save_to_hit_at": current_time + timedelta(minutes=1),
                    "blacklisted_at": current_time + timedelta(minutes=3),
                },
            )

            response.message = f"OTP sent to {account_record.phone_number}."
            response.data = UniqueId(unique_id=unique_id)
    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["POST"],
    path="/phone-number/{unique_id}",
    endpoint=send_otp_phone_number_endpoint,
    response_model=ResponseDefault,
    status_code=status.HTTP_200_OK,
    summary="Send otp phone number.",
)
