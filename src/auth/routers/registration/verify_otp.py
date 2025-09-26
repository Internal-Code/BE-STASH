import traceback
from uuid import UUID
from typing import Any, cast
from fastapi import APIRouter, status, Depends, HTTPException
from errors.custom_error import (
    BaseError,
    NotFoundError,
    InvalidInputError,
    FeatureNotImplementedError,
)
from utils.logger import logging
from utils.time import local_time
from services.postgre.connection import get_db
from services.postgre.query_schema import Filters, SelectData
from services.postgre.query import DatabaseQuery
from services.postgre.attribute_type import SendOtpChannelEnum
from services.postgre.models import (
    Users,
    UserRegistrationStates,
    OtpRequests,
    PinResets,
    Countries,
)
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from src.schema.enum import OtpRequestTypeEnum
from src.schema.payload import VerificationOtpPayload
from src.schema.response import (
    BaseResponse,
    UserRegisterStateResponse,
    UserRegisterStateStepsResponse,
)

router = APIRouter(tags=["User Register"], prefix="/user")


async def verify_otp_endpoint(
    schema: VerificationOtpPayload, db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    u = aliased(Users)
    or2 = aliased(OtpRequests)
    urs = aliased(UserRegistrationStates)
    pr = aliased(PinResets)
    c = aliased(Countries)

    session = DatabaseQuery(db)

    response = BaseResponse()
    user_state = UserRegisterStateResponse()
    user_steps = UserRegisterStateStepsResponse()

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
                cast(ColumnElement[Any], pr.id).label("pin_reset_id"),
                cast(ColumnElement[Any], or2.otp_code).label("otp_code"),
                cast(ColumnElement[Any], or2.expired_at).label("expired_at"),
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
        user_register_state_id = user_data["user_register_state_id"]
        otp_code = user_data["otp_code"]
        expired_at = user_data["expired_at"]

        if current_time > expired_at:
            raise InvalidInputError(
                message="OTP code has expired. Please request new OTP code."
            )

        if schema.otp_code != otp_code:
            raise InvalidInputError(message="Invalid OTP code.")

        # Data preparation
        user_state_data: dict[str, Any] = {
            "updated_at": current_time,
            "phone_number_verified": 1,
        }
        new_otp_data: dict[str, Any] = {
            "updated_at": current_time,
            "used_at": current_time,
        }

        # Map target field
        match schema.request_type:
            case OtpRequestTypeEnum.register_user:
                target_field = or2.registration_state_id
                target_value = user_register_state_id
            case _:
                raise FeatureNotImplementedError(
                    message="This feature is not implemented."
                )

        # Update entry
        await session.update(
            master_table=urs,
            filters=Filters(
                filters=[
                    Filters(field_name=urs.user_id, filter_type="equal", value=user_id)
                ]
            ),
            values=user_state_data,
        )
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

        user_steps.phone_number_verified = True
        user_state.user_uid = UUID(user_uid)
        user_state.steps = user_steps

        response.message = "OTP verified successfully."
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
    methods=["PATCH"],
    path="/verify-otp",
    response_model=BaseResponse,
    endpoint=verify_otp_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Verify user OTP",
    description="Validates a user’s OTP during registration, ensuring correct type, channel, and expiry before marking verification.",
)
