from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt import get_current_user
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import UserPhoneNumber
from src.schema.custom_state import RegisterAccountState
from utils.query.general import update_record, find_record
from services.postgres.models import User, SendOtp
from utils.whatsapp_api import send_otp_whatsapp
from utils.generator import random_number
from utils.helper import local_time
from datetime import timedelta
from utils.custom_error import (
    EntityForceInputSameDataError,
    EntityAlreadyExistError,
    UserNotVerifiedError,
    ServiceError,
    StashBaseApiError,
    InvalidOperationError,
)
# from utils.database.general import (
#     local_time,
#     is_using_registered_phone_number,
#     update_user_phone_number,
#     save_otp_data,
#     extract_data_otp,
# )

router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def change_phone_number_endpoint(
    schema: UserPhoneNumber,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()
    generated_otp = random_number(6)
    registered_phone_number = await find_record(db=db, table=User, phone_number=schema.phone_number)
    otp_record = await find_record(db=db, table=SendOtp, unique_id=current_user.unique_id)

    try:
        logging.info("Endpoint update user phone number.")
        if registered_phone_number:
            raise EntityAlreadyExistError(detail="Phone number already used.")

        if schema.phone_number == current_user.phone_number:
            raise EntityForceInputSameDataError(detail="Cannot use same phone number.")

        if current_user.register_state == RegisterAccountState.ON_PROCESS:
            raise UserNotVerifiedError(detail="User should be validated, before changing phone number.")

        if current_time < otp_record.save_to_hit_at:
            logging.info("User should wait API cooldown.")
            raise InvalidOperationError(detail="Should wait in 1 minutes.")

        if current_time > otp_record.save_to_hit_at:
            logging.info("Matched condition. Sending OTP using whatsapp API.")

            await send_otp_whatsapp(phone_number=schema.phone_number, generated_otp=generated_otp)
            await update_record(
                db=db,
                table=SendOtp,
                conditions={"unique_id": current_user.unique_id},
                data={
                    "updated_at": current_time,
                    "otp_number": generated_otp,
                    "current_api_hit": otp_record.current_api_hit + 1 if otp_record.current_api_hit else 1,
                    "save_to_hit_at": current_time + timedelta(minutes=1),
                    "blacklisted_at": current_time + timedelta(minutes=3),
                },
            )
            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": current_user.unique_id},
                data={"updated_at": current_time, "phone_number": schema.phone_number},
            )

            response.message = "Update phone number success."
            response.data = UniqueId(unique_id=current_user.unique_id)

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number",
    endpoint=change_phone_number_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user phone number.",
)
