from uuid import uuid4
from datetime import timedelta
from src.secret import Config
from utils.logger import logging
from utils.smtp import send_gmail
from utils.helper import local_time
from utils.generator import random_number
from src.schema.response import ResponseToken
from fastapi.templating import Jinja2Templates
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import User, SendOtp
from src.schema.validator import FullNameValidatorMixin
from utils.sso.general import google_oauth_configuration
from fastapi import APIRouter, status, Depends, Request, BackgroundTasks
from authlib.integrations.starlette_client import OAuthError
from utils.custom_error import ServiceError, StashBaseApiError
from src.schema.custom_state import RegisterAccountState
from utils.jwt import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from utils.query.general import insert_record, find_record, update_record


config = Config()
router = APIRouter(tags=["User Register"], prefix="/user/register")


async def google_sso_auth_endpoint(
    request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> ResponseToken:
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
                "email_activation.html",
                context={
                    "request": {},
                    "full_name": validated_full_name,
                    "email": user_info.email,
                    "pin": generated_pin,
                },
            ).body.decode("utf-8")

            background_tasks.add_task(
                send_gmail,
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
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/google/auth",
    endpoint=google_sso_auth_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)
