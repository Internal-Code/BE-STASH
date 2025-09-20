from typing import Annotated
from src.secret import Config
from utils.logger import logging
from utils.helper import local_time
from utils.smtp import send_gmail
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, status, Depends, BackgroundTasks
from src.schema.response import ResponseDefault
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.model import User, BlacklistToken, UserToken
from utils.query import QueryDatabase
from src.schema.request_format import UpdatePinPayload
from utils.whatsapp_api import send_whatsapp
from utils.jwt import JWTHandler
from utils.error import (
    EntityForceInputSameDataError,
    ServiceError,
    StashBaseApiError,
    EntityDoesNotMatchedError,
)

config = Config()
jwt_handler = JWTHandler()
router = APIRouter(tags=["User Update Account"], prefix="/user/update")


async def update_pin_endpoint(
    schema: UpdatePinPayload,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Update PIN endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)

    current_time = local_time()

    validate_existing_pin = jwt_handler.verify_pin(
        pin=schema.current_pin, hashed_pin=current_user.pin
    )
    duplicated_updated_pin = jwt_handler.verify_pin(
        pin=schema.updated_pin, hashed_pin=current_user.pin
    )
    duplicated_confirmed_pin = jwt_handler.verify_pin(
        pin=schema.confirmed_new_pin, hashed_pin=current_user.pin
    )
    hashed_pin = jwt_handler.get_password_hash(password=schema.updated_pin)

    token_record = await query.find(
        table=UserToken, order_by="desc", unique_id=current_user.unique_id
    )

    templates = Jinja2Templates(directory="templates")

    try:
        if not validate_existing_pin:
            logging.error("Invalid PIN.")
            raise EntityDoesNotMatchedError(detail="Invalid existing PIN.")

        if schema.updated_pin != schema.confirmed_new_pin:
            logging.error("Updated PIN and confirmation PIN should be equal.")
            raise EntityDoesNotMatchedError(
                detail="Updated PIN and confirmation PIN should be equal."
            )

        if duplicated_updated_pin and duplicated_confirmed_pin:
            logging.error("Should update into different PIN.")
            raise EntityForceInputSameDataError(
                detail="Should update into different PIN."
            )

        await query.update(
            table=User,
            condition={"unique_id": current_user.unique_id},
            data={"pin": hashed_pin, "updated_at": current_time},
        )

        await query.insert(
            table=BlacklistToken,
            data={
                "unique_id": current_user.unique_id,
                "access_token": token_record.access_token,
                "refresh_token": token_record.refresh_token,
            },
        )

        if current_user.verified_email and current_user.verified_phone_number:
            logging.info(
                f"Sending updated information into {current_user.email} and {current_time.phone_number}."
            )
            email_body = templates.TemplateResponse(
                "update_pin_email_and_phone_number.html",
                context={
                    "request": {},
                    "full_name": current_user.full_name,
                    "phone_number": current_user.phone_number,
                    "email": current_user.email,
                    "pin": schema.confirmed_new_pin,
                },
            ).body.decode("utf-8")

            logging.info(
                f"Sending updated account into {current_user.email} and {current_user.phone_number}."
            )
            background_tasks.add_task(
                send_gmail,
                email_subject="Updated STASH PIN!",
                email_receiver=current_user.email,
                email_body=email_body,
            )

            background_tasks.add_task(
                send_whatsapp,
                message_template=(
                    "Dear *{full_name}*,\n\n"
                    "We are pleased to inform you that your PIN has been successfully changed. "
                    "You can now log in using email or phone number:\n\n"
                    f"Phone Number: *{current_user.phone_number}*\n"
                    f"Email: *{current_user.email}*\n"
                    "PIN: *{pin}*\n\n"
                    "Please ensure that you keep your account information secure.\n\n"
                    "Best Regards,\n"
                    "*Support Team*"
                ),
                full_name=current_user.full_name,
                phone_number=current_user.phone_number,
                pin=schema.confirmed_new_pin,
            )
        elif current_user.verified_email:
            logging.info(f"Sending updated information into {current_user.email}.")
            email_body = templates.TemplateResponse(
                "update_pin_email.html",
                context={
                    "request": {},
                    "full_name": current_user.full_name,
                    "email": current_user.email,
                    "confirmed_pin": schema.confirmed_new_pin,
                },
            ).body.decode("utf-8")

            logging.info(f"Sending updated account into {current_user.email}.")
            background_tasks.add_task(
                send_gmail,
                email_subject="Updated STASH PIN!",
                email_receiver=current_user.email,
                email_body=email_body,
            )
        else:
            logging.info(f"Sending updated account into {current_user.phone_number}.")
            background_tasks.add_task(
                send_whatsapp,
                message_template=(
                    "Dear *{full_name}*,\n\n"
                    "We are pleased to inform you that your PIN has been successfully changed. "
                    "You can now log in using the following credentials:\n\n"
                    "Phone Number: *{phone_number}*\n"
                    "PIN: *{pin}*\n\n"
                    "Please ensure that you keep your account information secure.\n\n"
                    "Best Regards,\n"
                    "*Support Team*"
                ),
                full_name=current_user.full_name,
                phone_number=current_user.phone_number,
                pin=schema.confirmed_new_pin,
            )

        response.message = "PIN successfully updated. User should performed re-login."

    except StashBaseApiError:
        raise

    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/pin",
    endpoint=update_pin_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user pin endpoint.",
)
