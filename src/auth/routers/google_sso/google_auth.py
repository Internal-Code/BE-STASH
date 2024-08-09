from src.auth.utils.logging import logging
from datetime import timedelta
from fastapi import APIRouter, status, HTTPException
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from src.auth.utils.sso.general import google_oauth_configuration
from authlib.integrations.starlette_client import OAuthError
from src.auth.schema.response import ResponseToken
from src.auth.utils.generator import random_number
from src.auth.utils.database.general import (
    is_using_registered_email, 
    save_google_sso_account
)
from src.secret import (
    ACCESS_TOKEN_EXPIRED, 
    REFRESH_TOKEN_EXPIRED
)
from src.auth.utils.database.general import (
    save_tokens
)
from src.auth.utils.jwt.security import (
    create_access_token,
    create_refresh_token,
    get_user
)

router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_auth(request: Request):
    try:
        response = ResponseToken()
        oauth = await google_oauth_configuration()
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google login failed.")

        request.session["userinfo"] = dict(user_info)
        registered_email = await is_using_registered_email(user_info.email)

        if not registered_email:
            await save_google_sso_account(
                username=user_info.given_name + str(random_number(8)),
                first_name=user_info.given_name,
                last_name=user_info.family_name,
                email=user_info.email,
            )
        print(user_info.email)
        user_in_db = await get_user(identifier=user_info.email)
        print(user_in_db.username)
        if user_in_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        access_token = await create_access_token(
            data={
                "sub": user_in_db.username,
                "user_uuid": str(user_in_db.user_uuid),
            },
            access_token_expires=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED)),
        )

        refresh_token = await create_refresh_token(
            data={
                "sub": user_in_db.username,
                "user_uuid": str(user_in_db.user_uuid),
            },
            refresh_token_expires=timedelta(minutes=int(REFRESH_TOKEN_EXPIRED)),
        )

        await save_tokens(
            user_uuid=user_in_db.user_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        
        response.access_token = access_token
        response.refresh_token = refresh_token

    except OAuthError as OauthErr:
        logging.error(f"Oauth error in google_sso_auth: {OauthErr}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth error: {OauthErr}"
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
    endpoint=google_sso_auth,
    status_code=status.HTTP_200_OK,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)