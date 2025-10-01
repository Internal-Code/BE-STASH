# TODO: should be revised
import traceback
from uuid import UUID
from typing import Any, cast
from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Request
from errors.custom_error import (
    BaseError,
    NotFoundError,
)
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func
from utils.network import get_client_ip
from utils.logger import logging
from utils.time import local_time
from utils.jwt import JwtConfig
from services.whatsapp.service import WhatsAppService
from services.postgre.query import DatabaseQuery
from services.postgre.query_schema import Filters, SelectData
from services.postgre.connection import get_db
from services.postgre.models import (
    UserRegistrationStates,
    Users,
    PinResets,
    OtpRequests,
    Countries,
)
from src.schema.payload import CreatePinPayload
from src.schema.response import BaseResponse, UserRegisterStateResponse

router = APIRouter(tags=["User Register"], prefix="/user")
jwt = JwtConfig()


async def create_pin_endpoint(
    request: Request,
    bg_task: BackgroundTasks,
    schema: CreatePinPayload,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    urs = aliased(UserRegistrationStates)
    pr = aliased(PinResets)
    or2 = aliased(OtpRequests)
    c = aliased(Countries)
    u = aliased(Users)

    session = DatabaseQuery(db)
    wa = WhatsAppService()

    current_time = local_time()

    response = BaseResponse()
    user_state = UserRegisterStateResponse()

    ip_address = get_client_ip(request)
    # otp_code = random_number(6)

    current_time = local_time()
    try:
        u_select = SelectData(
            entry=[
                cast(ColumnElement[Any], u.id).label("user_id"),
                cast(ColumnElement[Any], u.uid).label("user_uid"),
                cast(ColumnElement[Any], u.pin).label("user_pin"),
                cast(ColumnElement[Any], u.name).label("user_name"),
                cast(ColumnElement[Any], u.email).label("user_email"),
                func.concat(c.dial_code, u.phone_number).label("user_phone_numbear"),
                cast(ColumnElement[Any], urs.id).label("user_register_state_id"),
                cast(ColumnElement[Any], urs.phone_number_verified).label(
                    "phone_number_verified"
                ),
                cast(ColumnElement[Any], urs.email_verified).label("email_verified"),
                cast(ColumnElement[Any], pr.id).label("pin_reset_id"),
                cast(ColumnElement[Any], or2.otp_code).label("otp_code"),
                cast(ColumnElement[Any], or2.expired_at).label("expired_at"),
                cast(ColumnElement[Any], or2.api_cooldown_at).label("api_cooldown_at"),
            ]
        )
        u_join = SelectData(
            entry=[
                [c, c.id == u.country_id],
                [pr, pr.user_id == u.id],
                [urs, urs.user_id == u.id],
                [
                    or2,
                    or_(or2.registration_state_id == urs.id, or2.pin_reset_id == pr.id),
                ],
            ]
        )
        u_filter = Filters(
            filters=[
                Filters(
                    field_name=u.uid, filter_type="equal", value=str(schema.user_uid)
                )
            ]
        )
        user_data: Any = await session.fetch(
            field_names=u_select,
            master_table=u,
            join_tables=u_join,
            filters=u_filter,
            fetch_type="one",
        )
        if not user_data:
            raise NotFoundError(message=f"User {schema.user_uid} not found.")

        user_id = user_data["user_id"]
        user_uid = user_data["user_uid"]
        user_name = user_data["user_name"]
        phone_number = user_data["user_phone_numbear"]

        bg_task.add_task(
            wa.send_whatsapp,
            user_id=user_id,
            ip_address=ip_address,
            phone_number=phone_number,
            message_template=(
                f"Dear *{user_name}*,\n\n"
                "We are pleased to inform you that your new account has been successfully registered. "
                "You can now log in using the following credentials:\n\n"
                f"Phone Number: *{phone_number}*\n"
                f"PIN: *{schema.pin}*\n\n"
                "Please ensure that you keep your account information secure.\n\n"
                "Best Regards,\n"
                "STASH Support Team"
            ),
            pin=schema.pin,
            user_name=user_name,
        )

        # Data preparation
        hashed_pin = jwt.to_hashed(pin=schema.pin)
        new_user_data: dict[str, Any] = {
            "updated_at": current_time,
            "pin": hashed_pin,
        }

        # Update entry
        # await session.update(
        #     master_table=or2,
        #     filters=Filters(
        #         filters=[
        #             Filters(
        #                 field_name=or2.registration_state_id,
        #                 filter_type="equal",
        #                 value=user_register_state_id,
        #             )
        #         ]
        #     ),
        #     values=new_otp_data,
        # )
        await session.update(
            master_table=u,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=u.uid,
                        filter_type="equal",
                        value=user_uid,
                    )
                ]
            ),
            values=new_user_data,
        )

        user_state.user_uid = UUID(user_uid)
        response.message = "Successfully fetched user registration state."
        response.data = user_state.model_dump()

    except BaseError:
        raise
    except Exception as e:
        logging.error(
            f"Unhandled exception while fetching registration state for user_id={schema.user_uid}: {e}\n"
            f"{traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/create-pin",
    endpoint=create_pin_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Update wrong account & resend OTP",
    description="Resends OTP via WhatsApp when a user corrects their account details, with cooldown and expiry checks.",
    response_model=BaseResponse,
)
