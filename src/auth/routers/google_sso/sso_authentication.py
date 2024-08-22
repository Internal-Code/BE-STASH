from datetime import timedelta
from src.auth.utils.logging import logging
from uuid_extensions import uuid7
from starlette.requests import Request
from src.auth.utils.request_format import AccountCreationType, AccountType
from src.auth.utils.sso.general import google_oauth_configuration
from authlib.integrations.starlette_client import OAuthError
from src.auth.schema.response import ResponseDefault, UniqueID, ResponseToken
from src.auth.utils.jwt.general import (
    get_user,
    create_access_token,
    create_refresh_token,
)
from src.auth.utils.database.general import save_google_sso_account
from fastapi import APIRouter, status, HTTPException
from src.secret import ACCESS_TOKEN_EXPIRED, REFRESH_TOKEN_EXPIRED


router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_auth_endpoint(request: Request) -> ResponseDefault | ResponseToken:
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
        registered_account = await get_user(email=user_info.email)

        try:
            if (
                registered_account
                and registered_account.verified_email
                and registered_account.verified_phone_number
                and registered_account.pin
            ):
                logging.info("User google sso already finished registration process.")

                try:
                    access_token = await create_access_token(
                        data={"sub": registered_account.user_uuid},
                        access_token_expires=timedelta(
                            minutes=int(ACCESS_TOKEN_EXPIRED)
                        ),
                    )
                    refresh_token = await create_refresh_token(
                        data={"sub": registered_account.user_uuid},
                        refresh_token_expires=timedelta(
                            minutes=int(REFRESH_TOKEN_EXPIRED)
                        ),
                    )

                    response = ResponseToken(
                        access_token=access_token, refresh_token=refresh_token
                    )

                except Exception as E:
                    logging.error(
                        f"Error while logging in with saved google account: {E}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_417_EXPECTATION_FAILED,
                        detail="Please perform relogin.",
                    )

                return response

            if registered_account:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already created. Please proceed into next process.",
                )

            google_type = AccountCreationType(account_type=AccountType.GOOGLE)
            logging.info("Creating new user using google sso.")
            await save_google_sso_account(
                user_uuid=register_account_uuid,
                email=user_info.email,
                account_type=google_type.account_type.value,
            )

            response = ResponseDefault(
                success=True,
                message="Account google sso successfully created.",
                data=UniqueID(unique_id=register_account_uuid),
            )

        except HTTPException as E:
            raise E

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
