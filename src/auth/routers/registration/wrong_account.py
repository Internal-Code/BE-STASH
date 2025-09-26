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
    MandatoryInputError,
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
from src.schema.enum import OtpRequestTypeEnum
from src.schema.payload import WrongAccountPayload
from src.schema.response import BaseResponse, UserRegisterStateResponse

router = APIRouter(tags=["User Register"], prefix="/user")


async def wrong_account_endpoint(
    request: Request,
    bg_task: BackgroundTasks,
    schema: WrongAccountPayload,
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

    current_time = local_time()
    try:
        data = None
        match schema.channel.value:
            case "whatsapp":
                if not schema.country_id:
                    raise MandatoryInputError(
                        message="User should pass country_id data."
                    )

                # Validate country
                country: Any = await session.fetch(
                    field_names=SelectData(
                        entry=[cast(ColumnElement[Any], c.dial_code).label("dial_code")]
                    ),
                    master_table=c,
                    filters=Filters(
                        filters=[
                            Filters(
                                field_name=c.id,
                                filter_type="equal",
                                value=schema.country_id,
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

                data = schema.phone_number
                logging.info(
                    f"User {schema.user_uid} requested phone number correction. "
                    f"New phone={country['dial_code']}{schema.phone_number}"
                )
            case _:
                # TODO: will be developed after smtp service refactored
                raise FeatureNotImplementedError(
                    message="Verify OTP via email is not implemented."
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
        phone_number = f"{country['dial_code']}{schema.phone_number}"
        user_register_state_id = user_data["user_register_state_id"]
        api_cooldown_at = user_data["api_cooldown_at"]
        phone_number_verified = user_data["phone_number_verified"]
        email_verified = user_data["email_verified"]

        if OtpRequestTypeEnum.register_user and phone_number_verified == 1:
            response.message = f"User {schema.user_uid} phone number already verified."
            return response

        if OtpRequestTypeEnum.verify_account and email_verified == 1:
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

        # Data preparation
        new_otp_data: dict[str, Any] = {
            "updated_at": current_time,
            "used_at": None,
            "api_cooldown_at": current_time + timedelta(minutes=1),
            "expired_at": current_time + timedelta(minutes=3),
            "otp_code": otp_code,
        }

        new_user_data: dict[str, Any] = {
            "updated_at": current_time,
        }

        match schema.channel.value:
            case "whatsapp":
                new_user_data["phone_number"] = data
            case _:
                # TODO: will be developed after smtp fixed
                new_user_data["email"] = data
                pass

        # Update entry
        await session.update(
            master_table=or2,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=or2.registration_state_id,
                        filter_type="equal",
                        value=user_register_state_id,
                    )
                ]
            ),
            values=new_otp_data,
        )
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
    path="/wrong-account",
    endpoint=wrong_account_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Update wrong account & resend OTP",
    description="Resends OTP via WhatsApp when a user corrects their account details, with cooldown and expiry checks.",
    response_model=BaseResponse,
)
