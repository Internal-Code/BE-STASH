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
from services.postgre.attribute_type import UserDeviceInfoEnum, SendOtpChannelEnum
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

    ip_address = get_client_ip(request)
    user_uid = uuid4()
    current_time = local_time()

    wa = WhatsAppService()
    session = DatabaseQuery(db)

    response = BaseResponse()
    user_state = UserRegisterStateResponse()

    otp_code = random_number(6)
    error: Dict[str, Any] = {}
    try:
        # Validate country
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
            raise NotFoundError(
                message="Country not found.",
                error={"country_id": "Country id not found."},
            )

        # Validate phone number uniqueness
        pn_data = await session.fetch(
            master_table=u,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=u.phone_number,
                        filter_type="equal",
                        value=schema.phone_number,
                    )
                ]
            ),
        )
        if pn_data:
            error["phone_number"] = "Phone number already registered."

        # Validate email uniqueness
        if schema.email:
            e_data = await session.fetch(
                master_table=u,
                filters=Filters(
                    filters=[
                        Filters(
                            field_name=u.email, filter_type="equal", value=schema.email
                        )
                    ]
                ),
            )
            if e_data:
                error["email"] = "Email already registered."

        if error:
            raise ConflictDataError(message="Conflict data found.", error=error)

        # Build user data
        user_data = Users(
            country_id=schema.country_id,
            name=schema.name,
            uid=str(user_uid),
            gender=schema.gender,
            email=schema.email,
            phone_number=schema.phone_number,
            device_info=UserDeviceInfoEnum.android,
        )

        # Build user register state data
        user_reg_state_data = UserRegistrationStates(
            users=user_data,
            email_verified=0,
            phone_number_verified=0,
            pin_created=0,
        )

        # Build OTP request data
        otp_request_data = OtpRequests(
            user_registration_states=user_reg_state_data,
            api_cooldown_at=current_time,
            otp_code=otp_code,
            channel=SendOtpChannelEnum.whatsapp,
        )

        # Insert all data in a single transaction
        await session.insert(table=u, data=user_data)
        await session.insert(table=urs, data=user_reg_state_data)
        await session.insert(table=or2, data=otp_request_data)

        # Send OTP via WhatsApp
        phone_number = f"{country['dial_code']}{schema.phone_number}"
        background_tasks.add_task(
            wa.send_whatsapp,
            user_id=user_data.id,
            ip_address=ip_address,
            phone_number=phone_number,
            message_template=(
                "Your verification code is *{otp_code}*. "
                "Please enter this code to complete your verification. "
                "Kindly note that this code will *expire in 3 minutes*."
            ),
            otp_code=otp_code,
        )
        user_state.user_uid = user_uid
        response.message = "Success register new user."
        response.data = user_state.model_dump()
    except BaseError:
        raise
    except Exception as e:
        logging.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
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
    summary="User registration.",
)
