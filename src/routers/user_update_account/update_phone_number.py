from typing import Annotated
from utils.jwt import JWTHandler
from datetime import timedelta
from utils.logger import logging
from utils.query import QueryDatabase
from utils.helper import local_time
from utils.generator import Generator
from utils.whatsapp_api import send_whatsapp
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.model import User, SendOtp
from src.schema.request_format import PhoneNumber
from src.schema.response import ResponseDefault, UniqueId
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    EntityForceInputSameDataError,
    EntityAlreadyExistError,
    UserNotVerifiedError,
    ServiceError,
    StashBaseApiError,
    InvalidOperationError,
    DataNotFoundError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def update_phone_number_endpoint(
    schema: PhoneNumber,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Update phone number endpoint.")
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)
    current_time = local_time()
    generated_otp = generator.random_number(6)
    otp_record = await query.find(table=SendOtp, unique_id=current_user.unique_id)

    try:
        if not otp_record:
            logging.error("OTP record not found")
            raise DataNotFoundError("OTP record not found.")

        remaining_time = otp_record.save_to_hit_at.second - current_time.second

        if current_user.phone_number != schema.phone_number:
            logging.info("User input different phone number.")
            registered_phone_number = await query.find(
                table=User, phone_number=schema.phone_number
            )
            if registered_phone_number:
                logging.error("Phone number already taken.")
                raise EntityAlreadyExistError(
                    detail="Phone number already taken. Please use another phone number."
                )

        if schema.phone_number == current_user.phone_number:
            logging.error("Cannot update into same phone number.")
            raise EntityForceInputSameDataError(
                detail="Should update into different phone number."
            )

        if not current_user.register_state:
            logging.error("User should be validated first.")
            raise UserNotVerifiedError(
                detail="User should be validated, before changing phone number."
            )

        if current_time < otp_record.save_to_hit_at:
            logging.info(f"Should wait for API cooldown {remaining_time}s.")
            raise InvalidOperationError(detail=f"Should wait in {remaining_time}s.")

        if current_time > otp_record.save_to_hit_at:
            logging.info("Sending OTP into phone number.")
            background_tasks.add_task(
                send_whatsapp,
                message_template=(
                    "Your verification code is *{generated_otp}*. "
                    "Please enter this code to complete your verification. "
                    "Kindly note that this code will *expire in 3 minutes*."
                ),
                phone_number=schema.phone_number,
                generated_otp=generated_otp,
            )

            await query.update(
                table=SendOtp,
                condition={"unique_id": current_user.unique_id},
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

            await query.update(
                table=User,
                condition={"unique_id": current_user.unique_id},
                data={
                    "updated_at": current_time,
                    "phone_number": schema.phone_number,
                    "otp_state": False,
                    "verified_phone_number": False,
                },
            )

            response.message = "Phone number successfully updated."
            response.data = UniqueId(unique_id=current_user.unique_id)

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number",
    endpoint=update_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Add or update user phone number.",
)
