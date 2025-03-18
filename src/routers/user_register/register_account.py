from uuid import uuid4
from datetime import timedelta
from utils.logger import logging
from utils.helper import local_time
from utils.query import QueryDatabase
from utils.generator import Generator
from utils.whatsapp_api import send_whatsapp
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from services.postgres.models import User, SendOtp
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import RegisterAccountPayload
from fastapi import (
    APIRouter, 
    status, 
    Depends, 
    BackgroundTasks
)
from utils.error import (
    ServiceError, 
    StashBaseApiError, 
    EntityAlreadyExistError
)

router = APIRouter(tags=["User Register"], prefix="/user/register")


async def register_account_endpoint(
    schema: RegisterAccountPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    generator = Generator()
    query = QueryDatabase(db)
    unique_id = str(uuid4())
    generated_otp = generator.random_number(6)
    response = ResponseDefault()

    phone_number_record = await query.find(table=User, phone_number=schema.phone_number)

    try:
        if phone_number_record:
            raise EntityAlreadyExistError(detail="Phone number already taken.")

        await query.insert(
            table=User,
            data={
                "unique_id": unique_id,
                "full_name": schema.full_name,
                "phone_number": schema.phone_number,
            },
        )

        await query.insert(
            table=SendOtp,
            data={
                "unique_id": unique_id,
                "otp_number": generated_otp,
                "save_to_hit_at": local_time(),
                "blacklisted_at": local_time() + timedelta(minutes=3),
                "current_api_hit": 1,
            },
        )

        logging.info("Sending OTP code.")
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

        response.message = "Account successfully created."
        response.data = UniqueId(unique_id=unique_id)

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["POST"],
    path="/new-account",
    response_model=ResponseDefault,
    endpoint=register_account_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Account registration.",
)
