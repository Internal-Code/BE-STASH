import traceback
from datetime import timedelta
from uuid import UUID
from typing import Any, cast
from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Request
from errors.custom_error import (
    BaseError,
    NotFoundError,
    FeatureNotImplementedError,
    ShouldWaitError,
)
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func
from utils.network import get_client_ip
from utils.logger import logging
from utils.time import local_time
from utils.generator import random_number
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
from services.postgre.attribute_type import SendOtpChannelEnum
from src.schema.enum import OtpRequestTypeEnum
from src.schema.payload import RequestNewOtpPayload
from src.schema.response import BaseResponse, UserRegisterStateResponse

router = APIRouter(tags=["User Register"], prefix="/user")


async def request_new_otp_endpoint(
    request: Request,
    bg_task: BackgroundTasks,
    schema: RequestNewOtpPayload,
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
    otp_code = random_number(6)

    error: dict[str, Any] = {}
    current_time = local_time()

    logging.info(
        f"[REQUEST_NEW_OTP] Incoming request from ip={ip_address}, "
        f"user_uid={schema.user_uid}, channel={schema.channel}, request_type={schema.request_type}"
    )

    try:
        # Validate request type
        if schema.channel != SendOtpChannelEnum.whatsapp:
            error["channel"] = "Verify OTP via email is not implemented."

        if schema.request_type != OtpRequestTypeEnum.register_user:
            error["request_type"] = (
                f"Verify OTP request {schema.request_type} not implemented."
            )

        if error:
            logging.warning(
                f"[REQUEST_NEW_OTP] Feature not implemented for user_uid={schema.user_uid} | error={error}"
            )
            raise FeatureNotImplementedError(
                message="Feature not implemented", error=error
            )

        logging.debug(f"[REQUEST_NEW_OTP] Fetching user data for uid={schema.user_uid}")

        u_select = SelectData(
            entry=[
                cast(ColumnElement[Any], u.id).label("user_id"),
                cast(ColumnElement[Any], u.uid).label("user_uid"),
                cast(ColumnElement[Any], u.email).label("user_email"),
                func.concat(c.dial_code, u.phone_number).label("user_phone_number"),
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
            logging.warning(f"[REQUEST_NEW_OTP] User not found: uid={schema.user_uid}")
            raise NotFoundError(message=f"User {schema.user_uid} not found.")

        user_id = user_data["user_id"]
        phone_number = user_data["user_phone_number"]
        api_cooldown_at = user_data["api_cooldown_at"]
        phone_number_verified = user_data["phone_number_verified"]
        email_verified = user_data["email_verified"]
        user_register_state_id = user_data["user_register_state_id"]

        logging.info(
            f"[REQUEST_NEW_OTP] User found uid={schema.user_uid}, phone={phone_number}"
        )

        if OtpRequestTypeEnum.register_user and phone_number_verified == 1:
            logging.info(
                f"[REQUEST_NEW_OTP] Phone already verified for uid={schema.user_uid}"
            )
            response.message = f"User {schema.user_uid} phone number already verified."
            return response

        if OtpRequestTypeEnum.verify_account and email_verified == 1:
            logging.info(
                f"[REQUEST_NEW_OTP] Email already verified for uid={schema.user_uid}"
            )
            response.message = f"User {schema.user_uid} email already verified."
            return response

        if current_time < api_cooldown_at:
            wait_seconds = int((api_cooldown_at - current_time).total_seconds())
            logging.warning(
                f"[REQUEST_NEW_OTP] Cooldown active for uid={schema.user_uid}, wait={wait_seconds}s"
            )
            raise ShouldWaitError(
                message=f"User should wait {wait_seconds}s before requesting new OTP."
            )

        logging.debug(
            f"[REQUEST_NEW_OTP] Sending OTP via WhatsApp uid={schema.user_uid}, phone={phone_number}"
        )

        bg_task.add_task(
            wa.send_whatsapp,
            user_id=user_id,
            ip_address=ip_address,
            phone_number=phone_number,
            message_template=(
                "Your verification code is *{otp_code}*. "
                "Please enter this code to complete your verification. "
                "Kindly note that this code will *expire in 3 minutes*."
            ),
            otp_code=otp_code,
        )

        # Map target field
        match schema.request_type.value:
            case "register_user":
                target_field = or2.registration_state_id
                target_value = user_register_state_id
            case _:
                logging.error(
                    f"[REQUEST_NEW_OTP] Unsupported request_type={schema.request_type}"
                )
                raise FeatureNotImplementedError(
                    message="This feature is not implemented."
                )

        new_otp_data: dict[str, Any] = {
            "updated_at": current_time,
            "used_at": None,
            "api_cooldown_at": current_time + timedelta(minutes=1),
            "expired_at": current_time + timedelta(minutes=3),
            "otp_code": otp_code,
        }

        await session.update(
            master_table=or2,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=target_field, filter_type="equal", value=target_value
                    )
                ]
            ),
            values=new_otp_data,
        )

        user_state.user_uid = UUID(user_data["user_uid"])
        response.message = "Registration state successfully fetched."
        response.data = user_state.model_dump()

        logging.info(
            f"[REQUEST_NEW_OTP] OTP generated successfully for uid={schema.user_uid}"
        )

    except BaseError:
        raise
    except Exception as e:
        logging.error(
            f"[REQUEST_NEW_OTP] Unhandled exception | error={e}\n"
            f"{traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/request-new-otp",
    endpoint=request_new_otp_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Request new OTP",
    description="Sends a new OTP via WhatsApp with cooldown and expiry checks, returning wait time if still active.",
    response_model=BaseResponse,
)
