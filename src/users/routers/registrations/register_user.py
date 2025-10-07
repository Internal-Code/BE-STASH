import traceback
from uuid import uuid4
from typing import Dict, Any, cast
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException, Request
from errors.custom_error import BaseError, NotFoundError, ConflictDataError
from utils.logger import logging
from utils.generator import random_number
from utils.time import local_time
from utils.network import get_client_ip
from services.postgre.connection import get_db
from services.postgre.attribute_type import (
    UserDeviceInfoEnum,
    SendOtpChannelEnum,
    ErrorLogTypeEnum,
)
from services.postgre.query_schema import Filters, SelectData
from services.postgre.query import DatabaseQuery
from services.whatsapp.service import WhatsAppService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from src.schema.response import BaseResponse, UserRegisterStateResponse
from src.schema.payload import RegisterUserPayload
from services.postgre.models import (
    Countries,
    Users,
    UserRegistrationStates,
    OtpRequests,
    ErrorLogs,
)

router = APIRouter(tags=["User Register"], prefix="/user")


async def register_user_endpoint(
    request: Request,
    schema: RegisterUserPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    c = aliased(Countries)
    u = aliased(Users)
    or2 = aliased(OtpRequests)
    urs = aliased(UserRegistrationStates)
    el = aliased(ErrorLogs)

    ip_address = get_client_ip(request)
    user_uid = uuid4()
    endpoint = str(request.url)
    current_time = local_time()

    wa = WhatsAppService()
    session = DatabaseQuery(db)

    response = BaseResponse()
    user_state = UserRegisterStateResponse()

    otp_code = random_number(6)
    error: Dict[str, Any] = {}

    logging.info("[REGISTER_USER] Starting registration")

    try:
        # Validate country
        logging.debug("[REGISTER_USER] Validating country")
        country: Any = await session.fetch(
            field_names=SelectData(
                entry=[cast(ColumnElement[Any], c.dial_code).label("dial_code")]
            ),
            master_table=c,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=c.id, filter_type="equal", value=schema.country_id
                    )
                ]
            ),
            fetch_type="one",
        )
        if not country:
            logging.warning("[REGISTER_USER] Country not found")
            raise NotFoundError("Country not found.")

        # Validate phone number uniqueness
        logging.debug("[REGISTER_USER] Checking phone number uniqueness")
        user_data: Any = await session.fetch(
            field_names=SelectData(
                entry=[
                    cast(ColumnElement[Any], u.phone_number).label("phone_number"),
                    cast(ColumnElement[Any], u.email).label("email"),
                ]
            ),
            master_table=u,
            filters=Filters(
                operator="or",
                filters=[
                    Filters(
                        field_name=u.phone_number,
                        filter_type="equal",
                        value=schema.phone_number,
                    ),
                    Filters(
                        field_name=u.email, filter_type="equal", value=schema.email
                    ),
                ],
            ),
        )

        phone_number = [entry["phone_number"] for entry in user_data]
        email = [entry["email"] for entry in user_data]

        logging.debug("Checking phone number uniqueness")
        if schema.phone_number in phone_number:
            logging.warning("[REGISTER_USER] Phone number already registered")
            error["phone_number"] = "Phone number already registered."

        logging.debug("Checking email uniqueness")
        if schema.email and schema.email in email:
            logging.warning("[REGISTER_USER] Email already registered")
            error["email"] = "Email already registered."

        if error:
            logging.error("[REGISTER_USER] Conflict data found")
            raise ConflictDataError(message="Conflict data found.", error=error)

        # Build user data
        logging.debug("[REGISTER_USER] Building user data")
        user_data = Users(
            country_id=schema.country_id,
            name=schema.name,
            uid=str(user_uid),
            gender=schema.gender,
            email=schema.email,
            phone_number=schema.phone_number,
            device_info=UserDeviceInfoEnum.android,
        )

        # Build user registration state data
        logging.debug("[REGISTER_USER] Preparing registration state")
        user_reg_state_data = UserRegistrationStates(
            users=user_data,
            email_verified=0,
            phone_number_verified=0,
            pin_created=0,
        )

        # Build OTP request data
        logging.debug("[REGISTER_USER] Generating OTP request")
        otp_request_data = OtpRequests(
            user_registration_states=user_reg_state_data,
            api_cooldown_at=current_time,
            otp_code=otp_code,
            channel=SendOtpChannelEnum.whatsapp,
        )

        # Insert all data in a single transaction
        logging.info(
            "[REGISTER_USER] Inserting user, registration state, and OTP request into DB"
        )
        await session.insert(table=u, data=user_data)
        await session.insert(table=urs, data=user_reg_state_data)
        await session.insert(table=or2, data=otp_request_data)

        # Send OTP via WhatsApp
        phone_number = f"{country['dial_code']}{schema.phone_number}"
        logging.info("[REGISTER_USER] Scheduling WhatsApp OTP send")
        background_tasks.add_task(
            wa.send_whatsapp,
            user_id=user_data.id,
            ip_address=ip_address,
            phone_number=phone_number,
            message_template=(
                "Your verification code is *{otp_code}*. Please enter this code to complete your verification. Kindly note that this code will *expire in 3 minutes*."
            ),
            otp_code=otp_code,
        )

        # Build response
        user_state.user_uid = user_uid
        response.message = "User successfully registered."
        response.data = user_state.model_dump()

        logging.info("[REGISTER_USER] User register completed")

    except BaseError as be:
        logging.error("[REGISTER_USER] Known application error", exc_info=True)
        error_data = ErrorLogs(
            ip_address=ip_address,
            type=ErrorLogTypeEnum.known_error,
            status_code=be.status_code,
            trace=traceback.format_exc(),
            endpoint=endpoint,
            payload=schema.model_dump(),
        )
        await session.insert(table=el, data=error_data)
        raise
    except Exception as exc:
        logging.error(
            f"[REGISTER_USER] Unhandled exception | error={exc}\n{traceback.format_exc()}"
        )
        error_data = ErrorLogs(
            ip_address=ip_address,
            type=ErrorLogTypeEnum.unknown_error,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            trace=traceback.format_exc(),
            endpoint=endpoint,
            payload=schema.model_dump(),
        )
        await session.insert(table=el, data=error_data)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    return response


router.add_api_route(
    methods=["POST"],
    path="/register",
    response_model=BaseResponse,
    endpoint=register_user_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Registers a new user, validates uniqueness, sets registration state, and sends OTP via WhatsApp.",
)
