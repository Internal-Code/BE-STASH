from datetime import timedelta
from uuid_extensions import uuid7
from fastapi import APIRouter, status
from starlette.requests import Request
from src.auth.utils.logging import logging
from src.auth.utils.validator import check_fullname
from src.auth.utils.generator import generate_full_name
from authlib.integrations.starlette_client import OAuthError
from src.auth.utils.sso.general import google_oauth_configuration
from src.secret import ACCESS_TOKEN_EXPIRED, REFRESH_TOKEN_EXPIRED
from src.auth.schema.response import ResponseDefault, UniqueID, ResponseToken
from src.auth.routers.exceptions import ServiceError, FinanceTrackerApiError
from src.auth.utils.database.general import (
    save_google_sso_account,
    save_otp_data,
    local_time,
)
from src.auth.utils.jwt.general import (
    get_user,
    create_access_token,
    create_refresh_token,
)


router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_auth_endpoint(request: Request) -> ResponseToken | ResponseDefault:
    oauth = await google_oauth_configuration()
    token = await oauth.google.authorize_access_token(request)

    try:
        user_info = token.get("userinfo")
        if not user_info:
            raise ServiceError(detail="Google login failed.", name="Google SSO")

        request.session["userinfo"] = dict(user_info)
        registered_account = await get_user(email=user_info.email)

        try:
            if not registered_account:
                logging.info("Creating new user using google sso.")
                register_account_uuid = str(uuid7())
                fullname = await generate_full_name(
                    first_name=user_info.given_name, last_name=user_info.family_name
                )
                validated_fullname = await check_fullname(value=fullname)

                logging.info("Save registered user via google sso.")
                await save_google_sso_account(
                    user_uuid=register_account_uuid,
                    email=user_info.email,
                    full_name=validated_fullname,
                )

                logging.info("Initialized OTP save data.")
                await save_otp_data(
                    user_uuid=register_account_uuid,
                    current_api_hit=1,
                    saved_by_system=True,
                    save_to_hit_at=local_time(),
                )

                response = ResponseDefault(
                    success=True,
                    message="Sucess registered new user via google sso.",
                    data=UniqueID(unique_id=register_account_uuid),
                )
                return response

            if not registered_account.verified_phone_number:
                logging.info("User should validated phone number first.")
                response = ResponseDefault(
                    success=True,
                    message="User should validated phone number.",
                    data=UniqueID(unique_id=registered_account.user_uuid),
                )
                return response

            if not registered_account.pin:
                logging.info("User should create pin first.")
                response = ResponseDefault(
                    success=True,
                    message="User should create pin.",
                    data=UniqueID(unique_id=registered_account.user_uuid),
                )
                return response

            if registered_account.pin:
                logging.info("User already created and verified.")

                access_token = await create_access_token(
                    data={"sub": registered_account.user_uuid},
                    access_token_expires=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED)),
                )
                refresh_token = await create_refresh_token(
                    data={"sub": registered_account.user_uuid},
                    refresh_token_expires=timedelta(minutes=int(REFRESH_TOKEN_EXPIRED)),
                )
                response = ResponseToken(
                    access_token=access_token, refresh_token=refresh_token
                )
                return response

        except FinanceTrackerApiError as FTE:
            raise FTE

        except Exception as E:
            raise ServiceError(detail=f"Service error: {E}.", name="Google SSO")

    except FinanceTrackerApiError as FTE:
        raise FTE

    except OAuthError as OauthErr:
        logging.error(f"Oauth error in google_sso_auth: {OauthErr}.")
        raise ServiceError(
            detail="SSO error, please perform relogin.",
        )

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")


router.add_api_route(
    methods=["GET"],
    path="/auth",
    endpoint=google_sso_auth_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)
