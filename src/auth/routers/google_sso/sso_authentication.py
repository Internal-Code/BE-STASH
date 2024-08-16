from src.auth.utils.logging import logging
from uuid_extensions import uuid7
from starlette.requests import Request
from src.auth.utils.sso.general import google_oauth_configuration
from authlib.integrations.starlette_client import OAuthError
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.jwt.general import get_user
from src.auth.utils.database.general import (
    is_using_registered_email,
    save_google_sso_account,
)
from fastapi import APIRouter, status, HTTPException


router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_auth_endpoint(request: Request) -> ResponseDefault:
    try:
        response = ResponseDefault()
        oauth = await google_oauth_configuration()
        token = await oauth.google.authorize_access_token(request)
        register_account_uuid = str(uuid7())

        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Google login failed."
            )

        request.session["userinfo"] = dict(user_info)
        registered_email = await is_using_registered_email(email=user_info.email)

        try:
            if registered_email is True:
                logging.info("User already created.")
                account = await get_user(email=user_info.email)

                try:
                    logging.info("User phone number is not verified.")
                    response.success = True
                    response.message = "Account google sso already saved."
                    response.data = UniqueID(unique_id=account.user_uuid)
                except Exception as E:
                    logging.error(
                        f"Error while logging in with saved google account: {E}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Please perform relogin.",
                    )
            else:
                await save_google_sso_account(
                    user_uuid=register_account_uuid, email=user_info.email
                )

                response.success = True
                response.message = "Account google sso successfully created."
                response.data = UniqueID(unique_id=register_account_uuid)

        except Exception as E:
            logging.error(f"Error while google sso authentication: {E}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error while google sso authentication: {E}",
            )

    except OAuthError as OauthErr:
        logging.error(f"Oauth error in google_sso_auth: {OauthErr}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO error, please perform relogin.",
        )

    except HTTPException as E:
        raise E

    except Exception as E:
        logging.error(f"Exception error in google_sso_auth: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["GET"],
    path="/auth",
    endpoint=google_sso_auth_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)
