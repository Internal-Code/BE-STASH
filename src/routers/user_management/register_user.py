from utils.logger import logging
from utils.query import QueryDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.model import Country, User, RegisterState, SendOtp
from services.postgre.attribute import Channel
from utils.generator import Generator
from utils.whatsapp_api import send_whatsapp
from src.schema.response import ResponseDefault
from src.schema.request_format import RegisterAccountPayload
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    EntityAlreadyExistError,
)

router = APIRouter(tags=["User Management"], prefix="/user/management")


async def register_user_endpoint(
    schema: RegisterAccountPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Register user endpoint.")
    query = QueryDatabase(db)
    generator = Generator()
    response = ResponseDefault()
    otp_code = generator.random_number(6)

    try:
        existing_phone_number = await query.find(User, phone_number=schema.phone_number)
        if existing_phone_number:
            raise EntityAlreadyExistError("Phone number already taken.", name="STASH")

        existing_email = await query.find(User, email=schema.email)
        if existing_email:
            raise EntityAlreadyExistError("Email already taken.", name="STASH")

        country_record = await query.find(Country, fetch="all")

        if not country_record:
            raise DataNotFoundError("Country data not found.")

        id_record = {entry["id"]: entry["dial_code"] for entry in country_record}
        if schema.country_id not in id_record:
            raise DataNotFoundError("Country id not found in database.")

        user = User(
            country_id=schema.country_id,
            first_name=schema.first_name,
            last_name=schema.last_name,
            email=schema.email,
            phone_number=schema.phone_number,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        register_state = RegisterState(user_id=user.id)
        db.add(register_state)
        await db.commit()
        await db.refresh(register_state)

        send_otp = SendOtp(
            register_id=register_state.id, otp_code=otp_code, channel=Channel.WHATSAPP
        )
        db.add(send_otp)
        await db.commit()

        full_phone = id_record[schema.country_id] + schema.phone_number
        background_tasks.add_task(
            send_whatsapp,
            message_template=(
                "Your verification code is *{generated_otp}*. "
                "Please enter this code to complete your verification. "
                "Kindly note that this code will *expire in 2 minutes*."
            ),
            phone_number=full_phone,
            generated_otp=otp_code,
        )

        response.message = f"Sending WhatsApp OTP to {full_phone}."

    except StashBaseApiError:
        raise
    except Exception as e:
        logging.exception(f"Unexpected error occurred: {e}.")
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/register",
    response_model=ResponseDefault,
    endpoint=register_user_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Account registration.",
)
