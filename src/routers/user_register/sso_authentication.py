from datetime import timedelta
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from fastapi import APIRouter, status
from starlette.requests import Request
from utils.logger import logging

# from utils.validator import check_fullname
from src.schema.validator import FullNameValidatorMixin
from authlib.integrations.starlette_client import OAuthError
from utils.sso.general import google_oauth_configuration
from src.secret import Config
from fastapi import Depends
from services.postgres.models import User, SendOtp
from utils.query.general import insert_record, find_record, update_record
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.smtp import send_gmail
from utils.helper import local_time
from src.schema.response import ResponseToken
from utils.custom_error import ServiceError, StashBaseApiError
from src.schema.custom_state import RegisterAccountState
from utils.generator import random_number

# from utils.database.general import (
#     save_google_sso_account,
#     save_otp_data,
#     local_time,
# )
from utils.jwt import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
)


config = Config()
router = APIRouter(tags=["User Register"], prefix="/user/register")


async def google_sso_auth_endpoint(request: Request, db: AsyncSession = Depends(get_db)) -> ResponseToken:
    response = ResponseToken()

    oauth = await google_oauth_configuration()
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")

    unique_id = str(uuid4())
    current_time = local_time()
    generated_pin = random_number(length=6)
    hashed_pin = get_password_hash(password=generated_pin)

    validated_full_name = FullNameValidatorMixin.validate_fullname(value=user_info.name)
    account_record = await find_record(db=db, table=User, email=user_info.email)

    templates = Jinja2Templates(directory="templates")

    try:
        if not user_info:
            raise ServiceError(detail="Google login failed.", name="Google SSO")

        if not account_record:
            await insert_record(
                db=db,
                table=User,
                data={
                    "unique_id": unique_id,
                    "full_name": validated_full_name,
                    "email": user_info.email,
                    "verified_email": True,
                },
            )

            await insert_record(
                db=db,
                table=SendOtp,
                data={"unique_id": unique_id, "save_to_hit_at": current_time, "blacklisted_at": current_time},
            )

            email_body = templates.TemplateResponse(
                "account_activation.html",
                context={
                    "request": {},
                    "full_name": validated_full_name,
                    "email": user_info.email,
                    "pin": generated_pin,
                },
            ).body.decode("utf-8")

            await send_gmail(
                email_receiver=user_info.email,
                email_subject="STASH Account Registration",
                email_body=email_body,
            )

            await update_record(
                db=db,
                table=User,
                conditions={"unique_id": unique_id},
                data={"pin": hashed_pin, "register_state": RegisterAccountState.SUCCESS},
            )

            access_token = create_access_token(
                data={"sub": unique_id},
                access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
            )
            refresh_token = create_refresh_token(
                data={"sub": unique_id},
                refresh_token_expires=timedelta(minutes=int(config.REFRESH_TOKEN_EXPIRED)),
            )

            logging.info("Success registered account via google sso.")
            response.access_token = access_token
            response.refresh_token = refresh_token
            return response
        else:
            access_token = create_access_token(
                data={"sub": account_record.unique_id},
                access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
            )
            refresh_token = create_refresh_token(
                data={"sub": account_record.unique_id},
                refresh_token_expires=timedelta(minutes=int(config.REFRESH_TOKEN_EXPIRED)),
            )
            logging.info("Success login account via google sso.")
            response.access_token = access_token
            response.refresh_token = refresh_token

    except StashBaseApiError:
        raise

    except OAuthError as OauthErr:
        logging.error(f"Oauth error in google_sso_auth: {OauthErr}.")
        raise ServiceError(detail="SSO error, please perform re-login.", name="Google SSO")

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["GET"],
    path="/google/auth",
    endpoint=google_sso_auth_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)
