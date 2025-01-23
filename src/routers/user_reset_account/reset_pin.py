from uuid import UUID
from src.secret import Config
from utils.jwt import JWTHandler
from utils.smtp import send_gmail
from utils.helper import local_time
from utils.query import QueryDatabase
from utils.whatsapp_api import send_whatsapp
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseDefault
from src.schema.request_format import UserResetPin
from services.postgres.models import User, ResetPin
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    InvalidOperationError,
)

config = Config()
jwt_handler = JWTHandler(config)
router = APIRouter(tags=["User Reset Account"], prefix="/user/reset-account")


async def reset_pin_endpoint(
    schema: UserResetPin,
    unique_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)

    current_time = local_time()

    hashed_pin = jwt_handler.get_password_hash(password=schema.pin)

    templates = Jinja2Templates(directory="templates")

    account_record = await query.find(table=User, unique_id=str(unique_id))
    reset_pin_record = await query.find(
        table=ResetPin, unique_id=account_record.unique_id
    )

    try:
        if not account_record:
            raise DataNotFoundError(detail="User not found.")

        if current_time > reset_pin_record.blacklisted_at:
            raise InvalidOperationError(detail="Reset pin token expired.")

        if schema.pin != schema.confirm_new_pin:
            raise InvalidOperationError(detail="PIN and Confirm PIN shoud be matched.")

        if current_time < reset_pin_record.blacklisted_at:
            if account_record.verified_email and account_record.verified_phone_number:
                email_body = templates.TemplateResponse(
                    "update_pin_email_and_phone_number.html",
                    context={
                        "request": {},
                        "full_name": account_record.full_name,
                        "phone_number": account_record.phone_number,
                        "email": account_record.email,
                        "pin": schema.confirm_new_pin,
                    },
                ).body.decode("utf-8")

                background_tasks.add_task(
                    send_gmail,
                    email_subject="Success Updated STASH PIN!",
                    email_receiver=account_record.email,
                    email_body=email_body,
                )

                background_tasks.add_task(
                    send_whatsapp,
                    phone_number=account_record.phone_number,
                    message_template=(
                        f"Dear *{account_record.full_name}*,\n\n"
                        "We would like to inform you that your PIN has been successfully changed.\n\n"
                        "Please use the following details to log in to your account:\n\n"
                        f"Phone Number: *{account_record.phone_number}*\n"
                        f"Email: *{account_record.email}*\n"
                        f"New PIN: *{schema.confirm_new_pin}*\n\n"
                        "For your security, please ensure you keep this information confidential.\n\n"
                        "Should you have any questions or require further assistance, feel free to contact our support team.\n\n"
                        "Best regards,\n"
                        "*STASH Support Team*"
                    ),
                )
            elif account_record.verified_phone_number:
                background_tasks.add_task(
                    send_whatsapp,
                    phone_number=account_record.phone_number,
                    message_template=(
                        f"Dear *{account_record.full_name}*,\n\n"
                        "We would like to inform you that your PIN has been successfully changed.\n\n"
                        "Please use the following details to log in to your account:\n\n"
                        f"Phone Number: *{account_record.phone_number}*\n"
                        f"New PIN: *{schema.confirm_new_pin}*\n\n"
                        "For your security, please ensure you keep this information confidential.\n\n"
                        "Should you have any questions or require further assistance, feel free to contact our support team.\n\n"
                        "Best regards,\n"
                        "*STASH Support Team*"
                    ),
                )
            else:
                email_body = templates.TemplateResponse(
                    "update_pin_email.html",
                    context={
                        "request": {},
                        "full_name": account_record.full_name,
                        "email": account_record.email,
                        "confirmed_pin": schema.confirm_new_pin,
                    },
                ).body.decode("utf-8")

                background_tasks.add_task(
                    send_gmail,
                    email_subject="Success Updated STASH PIN!",
                    email_receiver=account_record.email,
                    email_body=email_body,
                )

            await query.update(
                table=User,
                condition={"unique_id": account_record.unique_id},
                data={"updated_at": current_time, "pin": hashed_pin},
            )

            response.message = "Success reset PIN."

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/reset-pin/{unique_id}",
    response_model=ResponseDefault,
    endpoint=reset_pin_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Create new pin from forgot pin endpoint.",
)
