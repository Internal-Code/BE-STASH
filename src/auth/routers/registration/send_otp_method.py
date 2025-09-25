import traceback
from typing import Any, cast
from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logging
from errors.custom_error import BaseError, NotFoundError
from services.postgre.query import DatabaseQuery
from services.postgre.query_schema import Filters, SelectData
from services.postgre.connection import get_db
from services.postgre.models import UserRegistrationStates
from src.schema.response import BaseResponse, SendOtpMethodResponse

router = APIRouter(tags=["User Register"], prefix="/user")


async def register_state_endpoint(
    user_id: int = Query(ge=1, description="Unique ID of the user"),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """
    Get the current OTP verification method availability for a user.
    """
    urs = aliased(UserRegistrationStates)
    session = DatabaseQuery(db)

    response = BaseResponse()
    user_method = SendOtpMethodResponse()

    logging.info(f"Fetching registration state for user_id={user_id}")

    try:
        rs_select = SelectData(
            entry=[
                cast(ColumnElement[Any], urs.email_verified).label("email_verified"),
                cast(ColumnElement[Any], urs.phone_number_verified).label(
                    "phone_number_verified"
                ),
            ]
        )
        rs_filter = Filters(
            filters=[
                Filters(
                    field_name=urs.user_id,
                    filter_type="equal",
                    value=user_id,
                ),
            ]
        )

        rs_data: Any = await session.fetch(
            field_names=rs_select,
            master_table=urs,
            filters=rs_filter,
            fetch_type="one",
        )

        if not rs_data:
            logging.warning(f"No registration state found for user_id={user_id}")
            raise NotFoundError(message="Register state data not found.")

        logging.info(f"Registration state fetched for user_id={user_id}: {rs_data}")

        user_method.phone_number_verified = rs_data["phone_number_verified"] == 1
        user_method.email_verified = rs_data["email_verified"] == 1
        response.message = "Successfully fetched user registration state."
        response.data = user_method.model_dump()

    except BaseError:
        raise
    except Exception as e:
        logging.error(
            f"Unhandled exception while fetching registration state for user_id={user_id}: {e}\n"
            f"{traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    return response


router.add_api_route(
    methods=["GET"],
    path="/otp-method",
    endpoint=register_state_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get user registration state",
    description="Fetches whether the user's email and phone number are verified. "
    "Useful for determining OTP send method availability.",
    response_model=BaseResponse,
)
