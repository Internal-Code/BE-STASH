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
    """
    Get the current OTP verification method availability for a user.
    """
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

    try:
        # Validate request type
        if schema.channel != SendOtpChannelEnum.whatsapp:
            error["channel"] = "Verify OTP via email is not implemented."

        if schema.request_type != OtpRequestTypeEnum.register_user:
            error["request_type"] = (
                f"Verify OTP request {schema.request_type} not implemented."
            )

        if error:
            raise FeatureNotImplementedError(
                message="Feature not implemented", error=error
            )

        u_select = SelectData(
            entry=[
                cast(ColumnElement[Any], u.id).label("user_id"),
                cast(ColumnElement[Any], u.uid).label("user_uid"),
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
        phone_number = user_data["user_phone_numbear"]
        user_register_state_id = user_data["user_register_state_id"]
        api_cooldown_at = user_data["api_cooldown_at"]
        phone_number_verified = user_data["phone_number_verified"]
        email_verified = user_data["email_verified"]

        if OtpRequestTypeEnum.register_user and phone_number_verified == 1:
            response.message = f"User {schema.user_uid} phone number already verified."
            return response

        if OtpRequestTypeEnum.verify_account and email_verified == 1:
            # TODO: will be activated when smtp service already refactored
            response.message = f"User {schema.user_uid} email already verified."
            return response

        if current_time < api_cooldown_at:
            wait_seconds = int((api_cooldown_at - current_time).total_seconds())
            raise ShouldWaitError(
                message=f"User should wait {wait_seconds}s before requesting new OTP."
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
                raise FeatureNotImplementedError(
                    message="This feature is not implemented."
                )

        # Data preparation
        new_otp_data: dict[str, Any] = {
            "updated_at": current_time,
            "used_at": None,
            "api_cooldown_at": current_time + timedelta(minutes=1),
            "expired_at": current_time + timedelta(minutes=3),
            "otp_code": otp_code,
        }

        # Update entry
        await session.update(
            master_table=or2,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=target_field,
                        filter_type="equal",
                        value=target_value,
                    )
                ]
            ),
            values=new_otp_data,
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
    path="/request-new-otp",
    endpoint=request_new_otp_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get user registration state",
    description="Fetches whether the user's email and phone number are verified. "
    "Useful for determining OTP send method availability.",
    response_model=BaseResponse,
)
