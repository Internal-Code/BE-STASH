from src.auth.utils.logging import logging
from uuid_extensions import uuid7
from starlette.requests import Request
from src.auth.utils.sso.general import google_oauth_configuration
from authlib.integrations.starlette_client import OAuthError
from src.auth.schema.response import ResponseDefault
from src.auth.utils.jwt.general import get_user
from src.auth.utils.database.general import (
    is_using_registered_email,
    save_google_sso_account,
)
from fastapi import APIRouter, status, HTTPException


router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_auth(request: Request) -> ResponseDefault:
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
                    response.data = {"unique_id": account.user_uuid}
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
                response.data = {"unique_id": register_account_uuid}

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
    endpoint=google_sso_auth,
    status_code=status.HTTP_200_OK,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)


# from src.secret import ACCESS_TOKEN_EXPIRED, REFRESH_TOKEN_EXPIRED
# from src.auth.utils.database.general import save_tokens
# from src.auth.utils.logging import logging
# from datetime import timedelta
# from starlette.requests import Request
# from src.auth.utils.sso.general import google_oauth_configuration
# from authlib.integrations.starlette_client import OAuthError
# from src.auth.schema.response import ResponseToken
# from src.auth.utils.forgot_password.general import send_gmail
# from src.auth.utils.database.general import (
#     is_using_registered_email,
#     save_google_sso_account,
# )
# from src.auth.utils.generator import (
#     random_password,
#     random_number,
#     random_sso_username
# )
# from fastapi import (
#     APIRouter,
#     status,
#     HTTPException
# )
# from src.auth.utils.jwt.general import (
#     create_access_token,
#     create_refresh_token,
#     get_user,
#     get_password_hash
# )


# router = APIRouter(tags=["google-sso"], prefix="/google")


# async def google_sso_auth(request: Request) -> ResponseToken:
#     try:
#         response = ResponseToken()
#         oauth = await google_oauth_configuration()
#         token = await oauth.google.authorize_access_token(request)
#         generated_password = random_password(8)
#         hashed_generated_password = await get_password_hash(password=generated_password)

#         user_info = token.get("userinfo")
#         if not user_info:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN, detail="Google login failed."
#             )

#         generated_username = random_sso_username(user_info.email)
#         request.session["userinfo"] = dict(user_info)
#         registered_email = await is_using_registered_email(user_info.email)

#         try:
#             if not registered_email:
#                 await save_google_sso_account(
#                     username=generated_username,
#                     first_name=user_info.given_name,
#                     last_name=user_info.family_name,
#                     email=user_info.email,
#                     password=hashed_generated_password
#                 )

#                 user_in_db = await get_user(identifier=user_info.email)

#                 if user_in_db is None:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
#                     )

#                 access_token = await create_access_token(
#                     data={
#                         "sub": user_in_db.username,
#                         "user_uuid": str(user_in_db.user_uuid),
#                     },
#                     access_token_expires=timedelta(minutes=int(ACCESS_TOKEN_EXPIRED)),
#                 )

#                 refresh_token = await create_refresh_token(
#                     data={
#                         "sub": user_in_db.username,
#                         "user_uuid": str(user_in_db.user_uuid),
#                     },
#                     refresh_token_expires=timedelta(minutes=int(REFRESH_TOKEN_EXPIRED)),
#                 )

#                 await save_tokens(
#                     user_uuid=user_in_db.user_uuid,
#                     access_token=access_token,
#                     refresh_token=refresh_token,
#                 )

#                 email_body = (
#                     f"Dear {user_info.email},<br><br>"
#                     f"We are delighted to inform you that your account has been successfully registered in our application. Below are your generated username and password, which you can use to log in:<br><br>"
#                     f"You may log in using either your username or registered email address, along with the password provided below.<br><br>"
#                     f"<b>Username: {generated_username}</b><br>"
#                     f"<b>Password: {generated_password}</b><br><br>"
#                     f"For your security, we strongly recommend changing your password at your earliest convenience.<br><br>"
#                     f"Thank you for choosing our service.<br><br>"
#                     f"Best regards,<br>"
#                     f"The Support Team"
#                 )


#                 await send_gmail(
#                     email_subject="Default Password",
#                     email_receiver=user_info.email,
#                     email_body=email_body
#                 )

#                 response.access_token = access_token
#                 response.refresh_token = refresh_token

#         except Exception as E:
#             logging.error(f"Error while google sso authentication: {E}")
#             raise HTTPException(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Error while google sso authentication: {E}"
#             )
#     except OAuthError as OauthErr:
#         logging.error(f"Oauth error in google_sso_auth: {OauthErr}.")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail=f"OAuth error: {OauthErr}"
#         )
#     except HTTPException as E:
#         raise E
#     except Exception as E:
#         logging.error(f"Exception error in google_sso_auth: {E}.")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal Server Error: {E}.",
#         )
#     return response


# router.add_api_route(
#     methods=["GET"],
#     path="/auth",
#     endpoint=google_sso_auth,
#     status_code=status.HTTP_200_OK,
#     summary="Authorization using google sso.",
#     name="google_sso_auth",
# )
