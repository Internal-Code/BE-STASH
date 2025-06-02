from uuid import UUID
from datetime import timedelta
from utils.logger import logging
from utils.helper import local_time
from utils.generator import Generator
from utils.query import QueryDatabase
from utils.whatsapp_api import send_whatsapp
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.model import User, SendOtp
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import PhoneNumber
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
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
    schema: PhoneNumber,
    unique_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)
    current_time = local_time()
    unique_id = str(unique_id)
    generated_otp = generator.random_number(6)
    current_user = await query.find(table=User, unique_id=unique_id)
    registered_phone_number = await query.find(
        table=User, phone_number=schema.phone_number
    )
    otp_record = await query.find(table=SendOtp, unique_id=unique_id)

    try:
        if not otp_record:
            logging.error("OTP record not found")
            raise DataNotFoundError("OTP record not found.")

        remaining_time = otp_record.save_to_hit_at.second - current_time.second

        if not current_user:
            logging.error("User not found.")
            raise DataNotFoundError(detail="User not found.")

        if current_user.register_state:
            logging.error("User already set PIN.")
            raise EntityAlreadyFilledError(detail="User already set PIN.")

        if current_user.phone_number == schema.phone_number:
            logging.error("Cannot changed into same phone number.")
            raise EntityForceInputSameDataError(
                detail="Should update into different phone number."
            )

        if registered_phone_number:
            logging.error("Phone number already taken.")
            raise EntityAlreadyExistError(
                detail="Phone number already taken. Please use another phone number."
            )

        if current_time < otp_record.save_to_hit_at:
            logging.info(f"Should wait for API cooldown {remaining_time}s.")
            raise InvalidOperationError(detail=f"Should wait in {remaining_time}s.")

        if current_time > otp_record.save_to_hit_at:
            logging.info(f"Sending OTP information into {current_user.phone_number}")
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

            await query.update(
                table=User,
                condition={"unique_id": unique_id},
                data={"phone_number": schema.phone_number, "updated_at": current_time},
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

            response.success = True
            response.message = "OTP sent into phone number."
            response.data = UniqueId(unique_id=current_user.unique_id)

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number/{unique_id}",
    response_model=ResponseDefault,
    endpoint=wrong_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Wrong registered user phone number.",
)
