from utils.logger import logging
from utils.query import QueryDatabase
from utils.generator import Generator
from utils.whatsapp_api import send_whatsapp
from services.postgre.connection import get_db
from services.postgre.attribute_type import Channel
from src.schema.response import ResponseDefault
from src.schema.request_format import RegisterAccountPayload
from fastapi import APIRouter, status, Depends, BackgroundTasks
from services.postgre.models import Countries, Users, RegisterStates, SendOtps
from sqlalchemy.ext.asyncio import AsyncSession
from errors.custom_error import BaseError

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
    errors = {}

    try:
        existing_phone_number = await query.find(
            Users, phone_number=schema.phone_number
        )
        if existing_phone_number:
            errors["phone_number"] = "Phone number already taken."

        existing_email = await query.find(Users, email=schema.email)
        if existing_email:
            errors["email"] = "Email already taken."

        country_record = await query.find(Countries, fetch="all")

        if not country_record:
            errors["country_id"] = "Country data not found."

        id_record = {entry["id"]: entry["dial_code"] for entry in country_record}

        if schema.country_id not in id_record:
            errors["country_id"] = "Country id not found in database."

        if errors:
            raise BaseError(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Entry already exists.",
                errors=errors,
            )

        user = Users(
            country_id=schema.country_id,
            first_name=schema.first_name,
            last_name=schema.last_name,
            email=schema.email,
            phone_number=schema.phone_number,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        register_state = RegisterStates(user_id=user.id)
        db.add(register_state)
        await db.commit()
        await db.refresh(register_state)

        send_otp = SendOtps(
            register_id=register_state.id, otp_code=otp_code, channel=Channel.whatsapp
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

    except BaseError:
        raise

    except Exception as e:
        logging.exception(f"Unexpected error occurred: {e}.")
        raise BaseError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal Server Error.",
            errors={"error": str(e)},
        )

    return response


router.add_api_route(
    methods=["POST"],
    path="/register",
    response_model=ResponseDefault,
    endpoint=register_user_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Account registration.",
)
