from datetime import timedelta
from utils.helper import local_time
from utils.generator import Generator
from utils.query import QueryDatabase
from utils.whatsapp_api import send_whatsapp
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import User, SendOtp
from src.schema.response import ResponseDefault, UniqueId
from src.schema.custom_state import RegisterAccountState
from src.schema.request_format import UserWrongPhoneNumber
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
    schema: UserWrongPhoneNumber,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    generator = Generator()
    query = QueryDatabase(db)

    current_time = local_time()
    generated_otp = generator.random_number(6)

    account_record = await query.find(table=User, unique_id=schema.unique_id)
    registered_phone_number = await query.find(
        table=User, phone_number=schema.phone_number
    )
    otp_record = await query.find(table=SendOtp, unique_id=schema.unique_id)

    try:
        if not account_record:
            raise DataNotFoundError(detail="Account not found.")

        if account_record.register_state == RegisterAccountState.SUCCESS:
            raise EntityAlreadyFilledError(detail="Account already set pin.")

        if account_record.phone_number == schema.phone_number:
            raise EntityForceInputSameDataError(
                detail="Cannot changed into same phone number."
            )

        if registered_phone_number:
            raise EntityAlreadyExistError(
                detail="Phone number already taken. Please use another phone number."
            )

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

            await query.update(
                table=User,
                condition={"unique_id": schema.unique_id},
                data={"phone_number": schema.phone_number, "updated_at": current_time},
            )

            await query.update(
                table=SendOtp,
                condition={"unique_id": schema.unique_id},
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
            response.message = "Sending OTP into updated phone number."
            response.data = UniqueId(unique_id=account_record.unique_id)

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/phone-number",
    response_model=ResponseDefault,
    endpoint=wrong_phone_number_endpoint,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Wrong registered account phone number.",
)
