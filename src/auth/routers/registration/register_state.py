import traceback
from utils.logger import logging
from typing import cast, Any
from fastapi import APIRouter, status, Depends, HTTPException
from errors.custom_error import BaseError, NotFoundError
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.query import DatabaseQuery
from services.postgre.query_schema import Filters, SelectData
from services.postgre.connection import get_db
from services.postgre.attribute_type import UserRegistrationStateEnum
from services.postgre.models import Users, UserRegistrationStates, Countries
from src.schema.dependencies import validate_phone_number
from src.schema.response import (
    BaseResponse,
    UserRegisterStateResponse,
    UserRegisterStateStepsResponse,
)

router = APIRouter(tags=["User Register"], prefix="/user")


async def register_state_endpoint(
    phone_number: str = Depends(validate_phone_number),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """
    Get the current registration state of a user based on their phone number.
    Returns which steps are completed (phone verification, PIN creation) and overall status.
    """
    u = aliased(Users)
    urs = aliased(UserRegistrationStates)
    c = aliased(Countries)

    response = BaseResponse()
    user_state = UserRegisterStateResponse()
    user_steps = UserRegisterStateStepsResponse()
    session = DatabaseQuery(db)
    logging.info(f"Fetching registration state for phone_number={phone_number}")
    try:
        pn_select = SelectData(
            entry=[
                func.concat(c.dial_code, u.phone_number).label("phone_number"),
                cast(ColumnElement[Any], urs.phone_number_verified).label(
                    "phone_number_verified"
                ),
                cast(ColumnElement[Any], urs.pin_created).label("pin_created"),
            ]
        )
        pn_join = SelectData(
            entry=[[urs, urs.user_id == u.id], [c, c.id == u.country_id]]
        )
        pn_filter = Filters(
            filters=[
                Filters(
                    field_name=func.concat(c.dial_code, u.phone_number),
                    filter_type="equal",
                    value=phone_number,
                ),
            ]
        )
        phone_number_data: Any = await session.fetch(
            field_names=pn_select,
            master_table=u,
            join_tables=pn_join,
            filters=pn_filter,
            fetch_type="one",
        )
        if not phone_number_data:
            raise NotFoundError(message="Phone number not found.")

        logging.info(f"Registration data fetched: {phone_number_data}")

        phone_verified = phone_number_data["phone_number_verified"]
        pin_created = phone_number_data["pin_created"]

        match (phone_verified, pin_created):
            case (1, 1):
                user_state.status = UserRegistrationStateEnum.completed
                user_steps.phone_number_verified = True
                user_steps.pin_created = True
            case (1, 0):
                user_state.status = UserRegistrationStateEnum.pending
                user_steps.phone_number_verified = True
                user_steps.pin_created = False
            case _:
                user_state.status = UserRegistrationStateEnum.pending
                user_steps.phone_number_verified = False
                user_steps.pin_created = False

        user_state.steps = user_steps
        data = user_state.model_dump()
        response.message = "Successfully fetched user registration state."
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
    methods=["GET"],
    path="/register-state",
    endpoint=register_state_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Search countries by name.",
    response_model=BaseResponse,
)
