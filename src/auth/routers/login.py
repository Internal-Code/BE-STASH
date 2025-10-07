from typing import cast, Any
from fastapi import APIRouter, status, Depends, Request
from errors.custom_error import NotFoundError, AuthenticationError
from utils.logger import logging
from utils.jwt import JWTConfig
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.query import DatabaseQuery
from services.postgre.query_schema import Filters, SelectData
from services.postgre.connection import get_db
from services.postgre.models import (
    Users,
    UserRegistrationStates,
    Countries,
    # UserLoginHistories,
    UserTokens,
    Roles,
)
from src.schema.payload import CreatePinPayload
from src.schema.response import TokenResponse

router = APIRouter(tags=["Auth"], prefix="/user")
jwt = JWTConfig()


async def login_endpoint(
    request: Request,
    schema: CreatePinPayload,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    u = aliased(Users)
    ut = aliased(UserTokens)
    # ulh = aliased(UserLoginHistories)
    urs = aliased(UserRegistrationStates)
    c = aliased(Countries)
    r = aliased(Roles)

    session = DatabaseQuery(db)
    # ip_address = get_client_ip(request)

    # endpoint = str(request.url)
    error = {}
    response = TokenResponse()
    logging.info("[LOGIN] Login user received")
    try:
        u_select = SelectData(
            entry=[
                cast(ColumnElement[Any], u.uid).label("uid"),
                cast(ColumnElement[Any], u.email).label("email"),
                cast(ColumnElement[Any], u.pin).label("pin"),
                func.concat(c.dial_code, u.phone_number).label("phone_number"),
                cast(ColumnElement[Any], urs.id).label("user_register_state_id"),
                cast(ColumnElement[Any], urs.phone_number_verified).label(
                    "phone_number_verified"
                ),
                cast(ColumnElement[Any], urs.email_verified).label("email_verified"),
                cast(ColumnElement[Any], r.id).label("role_id"),
            ]
        )
        u_join = SelectData(
            entry=[
                [c, c.id == u.country_id],
                [urs, urs.user_id == u.id],
                [ut, ut.user_id == u.id],
                [r, r.id == ut.user_id],
            ]
        )
        u: Any = await session.fetch(
            field_names=u_select,
            master_table=u,
            join_tables=u_join,
            filters=Filters(
                filters=[Filters(field_name=u.uid, value=str(schema.user_uid))]
            ),
            fetch_type="one",
        )

        logging.debug(f"[LOGIN] Validating user_uid={schema.user_uid}")
        if not u:
            logging.error(f"[LOGIN] User not found | user_uid={schema.user_uid}")
            raise NotFoundError(message="User not found.")

        verified_phone_num = u["phone_number_verified"]
        phone_num = u["phone_number"]
        user_pin = u["user_pin"]

        logging.debug(f"[LOGIN] Validating phone number={phone_num}")
        if not verified_phone_num:
            logging.error("User should verify phone number first")
            error["phone_number"] = "User should verify phone number first"

        logging.debug(f"[LOGIN] Validating phone number={phone_num}")
        if not user_pin:
            logging.error("User should create pin first")
            error["pin"] = "User should create pin first"

        if error:
            raise AuthenticationError("User should verify create pin first", error)

        logging.info("[LOGIN] Generating token.")
        access_token = jwt.create_token(u, "access")
        access_token = jwt.create_token(u, "refresh")

        await session.insert(table=ut, data=error)

        response.access_token = access_token
        # response.refresh_token = refresh_token

    # except StashBaseApiError:
    #     raise
    except Exception:
        pass
        # raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/login",
    # response_model=ResponseToken,
    endpoint=login_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Authenticate users and return access token.",
)
