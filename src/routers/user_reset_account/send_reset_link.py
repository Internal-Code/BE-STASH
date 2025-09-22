from uuid import UUID
from datetime import timedelta
from src.secret import Config
from utils.logger import logging
from utils.smtp import send_gmail
from utils.time import local_time
from utils.query import QueryDatabase
from utils.whatsapp_api import send_whatsapp
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.model import User, ResetPin
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import SendResetLinkPayload
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
    DataNotFoundError,
    InvalidOperationError,
)

config = Config()
router = APIRouter(tags=["User Reset Account"], prefix="/user/reset-account")


async def send_reset_link_endpoint(
    schema: SendResetLinkPayload,
    unique_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Send reset link endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    current_time = local_time()
    unique_id = str(unique_id)
    reset_link = (
        f"http://localhost:8000/api/v1/user/reset-account/reset-pin/{unique_id}"
    )

    templates = Jinja2Templates(directory="templates")

    try:
        account_record = await query.find(table=User, unique_id=unique_id)

        if not account_record:
            logging.error("User not found.")
            raise DataNotFoundError(detail="User not found.")

        if not account_record.pin:
            logging.error("User is not created pin.")
            raise MandatoryInputError(detail="Should create pin first.")

        reset_pin_record = await query.find(
            table=ResetPin, unique_id=account_record.unique_id
        )
        if not reset_pin_record:
            logging.error("Reset pin not found.")
            raise DataNotFoundError(detail="Reset pin data not found.")

        remaining_time = reset_pin_record.save_to_hit_at.second - current_time.second

        if current_time < reset_pin_record.save_to_hit_at:
            logging.info(f"Should wait for API cooldown {remaining_time}s.")
            raise InvalidOperationError(detail=f"Should wait in {remaining_time}s.")

        if schema.method == schema.method.EMAIL:
            if not account_record.email:
                logging.error("User is not add an email.")
                raise MandatoryInputError(detail="Should add email first.")

            if not account_record.verified_email:
                logging.error("User email is not verified.")
                raise InvalidOperationError(detail="Email not verified.")

            if current_time > reset_pin_record.save_to_hit_at:
                logging.info("Sending reset pin into email.")
                email_body = templates.TemplateResponse(
                    "send_reset_link.html",
                    context={
                        "request": {},
                        "full_name": account_record.full_name,
                        "reset_link": reset_link,
                    },
                ).body.decode("utf-8")

                background_tasks.add_task(
                    send_gmail,
                    email_receiver=account_record.email,
                    email_subject="Reset Password",
                    email_body=email_body,
                )

                await query.update(
                    table=ResetPin,
                    condition={"unique_id": account_record.unique_id},
                    data={
                        "save_to_hit_at": current_time + timedelta(minutes=1),
                        "blacklisted_at": current_time + timedelta(minutes=5),
                    },
                )

                response.message = (
                    f"Password reset link sent to {account_record.email}."
                )
                response.data = UniqueId(unique_id=account_record.unique_id)
        else:
            if not account_record.phone_number:
                logging.error("User is not add phone number.")
                raise MandatoryInputError(detail="Should add phone number first.")

            if not account_record.verified_phone_number:
                logging.error("User phone number is not verified.")
                raise InvalidOperationError(detail="Phone number not verified.")

            if current_time > reset_pin_record.save_to_hit_at:
                logging.info("Sending reset pin into phone number.")
                background_tasks.add_task(
                    send_whatsapp,
                    phone_number=account_record.phone_number,
                    message_template=(
                        f"Dear *{account_record.full_name}*,\n\n"
                        "We received a request to reset your password. Please click the link below to create a new password:\n\n"
                        f"{reset_link}\n\n"
                        "Please note, this password reset link is only valid for *5 minutes*. If you did not request a password reset, please ignore this message.\n\n"
                        "Thank you,\n\n"
                        "Best regards,\n"
                        "*STASH Support Team*"
                    ),
                )

                await query.update(
                    table=ResetPin,
                    condition={"unique_id": account_record.unique_id},
                    data={
                        "save_to_hit_at": current_time + timedelta(minutes=1),
                        "blacklisted_at": current_time + timedelta(minutes=5),
                    },
                )

                response.message = (
                    f"Password reset link sent to {account_record.phone_number}."
                )
                response.data = UniqueId(unique_id=account_record.unique_id)

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/send-link/{unique_id}",
    response_model=ResponseDefault,
    endpoint=send_reset_link_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send forgot pin reset link.",
)
