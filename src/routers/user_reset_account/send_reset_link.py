from datetime import timedelta
from src.secret import Config
from utils.helper import local_time
from utils.whatsapp_api import send_whatsapp
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from services.postgres.models import User, ResetPin
from src.schema.response import ResponseDefault, UniqueId
from src.schema.request_format import SendVerificationLink
from utils.query import find_record, update_record
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.smtp import send_gmail
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
    schema: SendVerificationLink,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()

    account_record = await find_record(db=db, table=User, unique_id=schema.unique_id)
    reset_pin_record = await find_record(
        db=db, table=ResetPin, unique_id=account_record.unique_id
    )
    reset_link = f"http://localhost:8000/api/v1/user/reset-account/reset-pin/{account_record.unique_id}"

    templates = Jinja2Templates(directory="templates")

    try:
        if not account_record:
            raise DataNotFoundError(detail="Account not found.")

        if not account_record.pin:
            raise MandatoryInputError(detail="Should create pin first.")

        if current_time < reset_pin_record.save_to_hit_at:
            raise InvalidOperationError(detail="Should wait in 1 minutes.")

        if schema.method == schema.method.EMAIL:
            if not account_record.email:
                raise MandatoryInputError(detail="Should add email first.")

            if not account_record.verified_email:
                raise InvalidOperationError(detail="Email not verified.")

            if current_time > reset_pin_record.save_to_hit_at:
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

                await update_record(
                    db=db,
                    table=ResetPin,
                    conditions={"unique_id": account_record.unique_id},
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
                raise MandatoryInputError(detail="Should add phone number first.")

            if not account_record.verified_phone_number:
                raise InvalidOperationError(detail="Phone number not verified.")

            if current_time > reset_pin_record.save_to_hit_at:
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

                await update_record(
                    db=db,
                    table=ResetPin,
                    conditions={"unique_id": account_record.unique_id},
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
    methods=["POST"],
    path="/send-link",
    response_model=ResponseDefault,
    endpoint=send_reset_link_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send forgot pin reset link.",
)
