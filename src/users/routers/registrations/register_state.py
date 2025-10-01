import traceback
from utils.logger import logging
from uuid import UUID
from typing import cast, Any
from fastapi import APIRouter, status, Depends, HTTPException, Query
from errors.custom_error import BaseError, NotFoundError
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
    country_id: int = Query(ge=1),
    phone_number: str = Depends(validate_phone_number),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    u = aliased(Users)
    urs = aliased(UserRegistrationStates)
    c = aliased(Countries)

    session = DatabaseQuery(db)

    response = BaseResponse()
    user_state = UserRegisterStateResponse()
    user_steps = UserRegisterStateStepsResponse()

    logging.info(
        f"[REGISTER_STATE] Request received | country_id={country_id}, phone_number={phone_number}"
    )

    try:
        # Validate country
        logging.debug(f"[REGISTER_STATE] Validating country_id={country_id}")
        country: Any = await session.fetch(
            field_names=SelectData(
                entry=[cast(ColumnElement[Any], c.dial_code).label("dial_code")]
            ),
            master_table=c,
            filters=Filters(
                filters=[
                    Filters(field_name=c.id, filter_type="equal", value=country_id)
                ]
            ),
            fetch_type="one",
        )
        if not country:
            logging.warning(
                f"[REGISTER_STATE] Country not found | country_id={country_id}"
            )
            raise NotFoundError(
                message="Country not found.",
                error={"country_id": "Country id not found."},
            )

        logging.debug(
            f"[REGISTER_STATE] Country validated | dial_code={country['dial_code']}"
        )

        # Fetch registration state
        logging.debug(
            f"[REGISTER_STATE] Fetching registration state | phone_number={phone_number}"
        )
        pn_select = SelectData(
            entry=[
                cast(ColumnElement[Any], u.uid).label("user_uid"),
                cast(ColumnElement[Any], urs.id).label("register_state_id"),
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
                    field_name=u.phone_number, filter_type="equal", value=phone_number
                )
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
            logging.warning(
                f"[REGISTER_STATE] Phone number not found | phone_number={phone_number}"
            )
            raise NotFoundError(message="Phone number not found.")

        logging.info(
            f"[REGISTER_STATE] User data fetched | user_uid={phone_number_data['user_uid']}"
        )

        phone_verified = phone_number_data["phone_number_verified"]
        pin_created = phone_number_data["pin_created"]
        user_uid = phone_number_data["user_uid"]

        # Build user state response
        match (phone_verified, pin_created):
            case (1, 1):
                logging.debug("[REGISTER_STATE] User has completed registration.")
                user_state.status = UserRegistrationStateEnum.completed
                user_steps.phone_number_verified = True
                user_steps.pin_created = True
            case (1, 0):
                logging.debug("[REGISTER_STATE] User pending PIN creation.")
                user_state.status = UserRegistrationStateEnum.pending
                user_steps.phone_number_verified = True
                user_steps.pin_created = False
            case _:
                logging.debug(
                    "[REGISTER_STATE] User pending phone verification and PIN."
                )
                user_state.status = UserRegistrationStateEnum.pending
                user_steps.phone_number_verified = False
                user_steps.pin_created = False

        user_state.user_uid = UUID(user_uid)
        user_state.steps = user_steps

        response.message = "Registration state successfully retrieved."
        response.data = user_state.model_dump()

        logging.info(
            f"[REGISTER_STATE] Completed | phone_number={phone_number}, "
            f"user_uid={user_uid}, status={user_state.status}"
        )

    except BaseError as e:
        logging.error(f"[REGISTER_STATE] Known application error | {e}", exc_info=True)
        raise
    except Exception as e:
        logging.error(
            f"[REGISTER_STATE] Unhandled exception | error={e}\n"
            f"{traceback.format_exc()}"
        )
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
    summary="Get registration state",
    description="Fetches a user’s registration progress, including phone verification, PIN setup, and overall status.",
    response_model=BaseResponse,
)
