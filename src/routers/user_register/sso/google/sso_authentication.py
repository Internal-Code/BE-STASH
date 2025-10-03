from uuid import uuid4
from src.secret import Config
from datetime import timedelta
from utils.logger import logging
from utils.jwt import JWTHandler
from utils.smtp import send_gmail
from utils.time import local_time
from utils.query import QueryDatabase
from utils.generator import Generator
from src.schema.response import ResponseToken
from fastapi.templating import Jinja2Templates
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.model import User, SendOtp
from src.schema.validator import FullNameValidatorMixin
from utils.error import ServiceError, StashBaseApiError
from utils.sso.google import google_oauth_configuration
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, status, Depends, Request, BackgroundTasks


config = Config()
jwt_handler = JWTHandler()
router = APIRouter(tags=["SSO"], prefix="/user/register")


async def sso_authentication_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseToken:
    logging.info("SSO auth endpoint.")
    response = ResponseToken()
    generator = Generator()
    query = QueryDatabase(db)

    oauth = await google_oauth_configuration()
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")

    unique_id = str(uuid4())
    current_time = local_time()
    generated_pin = generator.random_number(6)
    hashed_pin = jwt_handler.get_password_hash(password=generated_pin)

    validated_full_name = FullNameValidatorMixin.validate_fullname(value=user_info.name)
    account_record = await query.find(table=User, email=user_info.email)

    templates = Jinja2Templates(directory="templates")

    try:
        if not user_info:
            logging.error("Unable to extract user info.")
            raise ServiceError(detail="Google login failed.", name="Google SSO")

        if not account_record:
            logging.info("New user detected.")
            await query.insert(
                table=User,
                data={
                    "unique_id": unique_id,
                    "full_name": validated_full_name,
                    "email": user_info.email,
                    "verified_email": True,
                },
            )

            await query.insert(
                table=SendOtp,
                data={
                    "unique_id": unique_id,
                    "save_to_hit_at": current_time,
                    "blacklisted_at": current_time,
                    "current_api_hit": 1,
                },
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
                email_subject="STASH User Registration",
                email_body=email_body,
            )

            await query.update(
                table=User,
                condition={"unique_id": unique_id},
                data={
                    "pin": hashed_pin,
                    "register_state": True,
                },
            )

            access_token = jwt_handler.create_access_token(
                data={"sub": unique_id},
                access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
            )
            refresh_token = jwt_handler.create_refresh_token(
                data={"sub": unique_id},
                refresh_token_expires=timedelta(days=int(config.REFRESH_TOKEN_EXPIRED)),
            )

            logging.info("New user successfully registered.")
            response.access_token = access_token
            response.refresh_token = refresh_token
            return response
        else:
            access_token = jwt_handler.create_access_token(
                data={"sub": account_record.unique_id},
                access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
            )
            refresh_token = jwt_handler.create_refresh_token(
                data={"sub": account_record.unique_id},
                refresh_token_expires=timedelta(days=int(config.REFRESH_TOKEN_EXPIRED)),
            )
            logging.info("User successfully logged in.")
            response.access_token = access_token
            response.refresh_token = refresh_token

    except StashBaseApiError:
        raise

    except OAuthError as OauthErr:
        logging.error(f"Oauth error in google_sso_auth: {OauthErr}.")
        raise ServiceError(detail="SSO error, please perform re-login.", name="Google SSO")

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/google/auth",
    endpoint=sso_authentication_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)
