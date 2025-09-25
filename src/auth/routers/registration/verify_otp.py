import traceback
from typing import Any, cast
from fastapi import APIRouter, status, Depends, HTTPException
from errors.custom_error import BaseError, NotFoundError, InvalidInputError
from utils.logger import logging
from utils.time import local_time
from utils.generator import random_number
from services.postgre.connection import get_db
from services.postgre.query_schema import Filters, SelectData
from services.postgre.query import DatabaseQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from src.schema.response import (
    BaseResponse,
    UserRegisterStateResponse,
    UserRegisterStateStepsResponse,
)
from src.schema.payload import VerificationOtpPayload
from services.postgre.models import (
    Users,
    UserRegistrationStates,
    OtpRequests,
    PinResets,
)

router = APIRouter(tags=["User Register"], prefix="/user")


async def verify_otp_endpoint(
    schema: VerificationOtpPayload, db: AsyncSession = Depends(get_db)
) -> BaseResponse:
    u = aliased(Users)
    or2 = aliased(OtpRequests)
    urs = aliased(UserRegistrationStates)
    pr = aliased(PinResets)

    session = DatabaseQuery(db)

    response = BaseResponse()
    user_state = UserRegisterStateResponse()
    user_steps = UserRegisterStateStepsResponse()

    current_time = local_time()
    otp_code = random_number(6)
    try:
        if schema.register_state_id is not None and schema.pin_reset_id is not None:
            raise InvalidInputError(
                message="Only one of register_state_id or pin_reset_id should be provided."
            )

        join_table = urs if schema.register_state_id is not None else pr
        column_table = (
            or2.registration_state_id
            if schema.register_state_id is not None
            else or2.pin_reset_id
        )

        o_select = SelectData(
            entry=[
                cast(ColumnElement[Any], u.id).label("user_id"),
                cast(ColumnElement[Any], or2.otp_code).label("otp_code"),
                cast(ColumnElement[Any], or2.expired_at).label("expired_at"),
            ]
        )
        o_join = SelectData(
            entry=[
                [join_table, join_table.id == column_table],
                [u, u.id == join_table.user_id],
            ]
        )
        o_filter = Filters(
            filters=[
                Filters(
                    field_name=or2.registration_state_id
                    if schema.register_state_id is not None
                    else or2.pin_reset_id,
                    filter_type="equal",
                    value=schema.register_state_id
                    if schema.register_state_id is not None
                    else schema.pin_reset_id,
                )
            ]
        )

        otp_data: Any = await session.fetch(
            field_names=o_select,
            master_table=or2,
            join_tables=o_join,
            filters=o_filter,
            fetch_type="one",
        )

        if not otp_data:
            raise NotFoundError(message="OTP request not found.")

        user_id = otp_data["user_id"]
        otp_code = otp_data["otp_code"]
        expired_at = otp_data["expired_at"]

        if current_time > expired_at:
            raise InvalidInputError(message="OTP code has expired.")

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

        # Update entry
        await session.update(
            master_table=urs,
            filters=Filters(
                filters=[Filters(field_name=u.id, filter_type="equal", value=user_id)]
            ),
            values=user_state_data,
        )
        await session.update(
            master_table=or2,
            filters=Filters(
                filters=[
                    Filters(
                        field_name=or2.registration_state_id
                        if schema.register_state_id is not None
                        else or2.pin_reset_id,
                        filter_type="equal",
                        value=schema.register_state_id
                        if schema.register_state_id is not None
                        else schema.pin_reset_id,
                    )
                ]
            ),
            values=new_otp_data,
        )
        user_steps.phone_number_verified = True
        user_steps.user_id = user_id
        user_steps.register_state_id = schema.register_state_id
        user_steps.pin_reset_id = schema.pin_reset_id
        user_state.steps = user_steps
        data = user_state.model_dump()

        response.message = "OTP verified successfully."
        response.data = data
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
    path="/verify-otp",
    response_model=BaseResponse,
    endpoint=verify_otp_endpoint,
    status_code=status.HTTP_200_OK,
    summary="User OTP verification.",
)
