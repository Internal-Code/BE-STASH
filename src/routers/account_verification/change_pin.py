import httpx
from typing import Annotated
from src.secret import Config
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from utils.validator import check_pin
from src.schema.response import ResponseDefault
from services.postgres.models import users, blacklist_tokens
from services.postgres.connection import database_connection
from utils.forgot_password.general import send_gmail
from utils.request_format import ChangePin, SendOTPPayload
from utils.database.general import local_time, extract_tokens
from utils.jwt.general import get_current_user, verify_pin, get_password_hash
from utils.custom_error import (
    EntityForceInputSameDataError,
    ServiceError,
    DatabaseError,
    FinanceTrackerApiError,
    EntityDoesNotMatchedError,
)

config = Config()
router = APIRouter(tags=["account-verification"], prefix="/change")


async def change_pin_endpoint(
    schema: ChangePin, current_user: Annotated[dict, Depends(get_current_user)]
) -> ResponseDefault:
    response = ResponseDefault()
    new_pin = await check_pin(pin=schema.change_pin)
    confirmed_pin = await check_pin(pin=schema.confirmed_changed_pin)
    valid_existing_pin = await verify_pin(
        pin=schema.current_pin, hashed_pin=current_user.pin
    )
    duplicated_changed_pin = await verify_pin(
        pin=schema.change_pin, hashed_pin=current_user.pin
    )
    duplicated_confirmed_pin = await verify_pin(
        pin=schema.confirmed_changed_pin, hashed_pin=current_user.pin
    )

    try:
        if not valid_existing_pin:
            raise EntityDoesNotMatchedError(detail="Invalid existing pin.")

        if new_pin != confirmed_pin:
            raise EntityDoesNotMatchedError(
                detail="The new PIN and confirmation PIN do not match. Please ensure both PINs are the same."
            )

        if duplicated_changed_pin and duplicated_confirmed_pin:
            raise EntityForceInputSameDataError(
                detail="New PIN cannot be the same as the current PIN. Please choose a different PIN."
            )

        hashed_pin = await get_password_hash(password=schema.change_pin)
        token_data = await extract_tokens(user_uuid=current_user.user_uuid)

        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(users.c.user_uuid == current_user.user_uuid)
                    .values(updated_at=local_time(), pin=hashed_pin)
                )

                blacklist_current_token = blacklist_tokens.insert().values(
                    blacklisted_at=local_time(),
                    user_uuid=current_user.user_uuid,
                    access_token=token_data.access_token,
                    refresh_token=token_data.refresh_token,
                )
                await session.execute(blacklist_current_token)
                await session.execute(query)
                await session.commit()
                logging.info("Success changed user pin and blacklisted current token.")
            except FinanceTrackerApiError as FE:
                raise FE
            except Exception as E:
                logging.error(f"Error while change_pin_endpoint: {E}.")
                await session.rollback()
                raise DatabaseError(
                    detail=f"Database error: {E}.",
                )
            finally:
                await session.close()

        if current_user.verified_email:
            logging.info("Account update information sent into email.")
            email_body = (
                f"Dear {current_user.full_name},<br><br>"
                f"We are pleased to inform you that your new account has been successfully updated pin.<br><br>"
                f"You can now log in using the following credentials:<br><br>"
                f"Phone Number: <strong>{current_user.phone_number}</strong><br>"
                f"PIN: <strong>{confirmed_pin}</strong><br><br>"
                f"Please ensure that you keep your account information secure.<br><br>"
                f"Thank you.<br><br>"
                f"Best regards,<br>"
                f"<strong>Support Team</strong>"
            )

            await send_gmail(
                email_subject="Success Updated New Pin!",
                email_receiver=current_user.email,
                email_body=email_body,
            )

            response.success = True
            response.message = "User successfully changed pin. Account information already sent into email."

        elif current_user.verified_phone_number:
            logging.info("Account update information sent into phone number.")
            payload = SendOTPPayload(
                phoneNumber=current_user.phone_number,
                message=(
                    f"Dear *{current_user.full_name}*,\n\n"
                    f"We are pleased to inform you that your pin has been successfully changed. "
                    f"You can now log in using the following credentials:\n\n"
                    f"Phone Number: *{current_user.phone_number}*\n"
                    f"PIN: *{confirmed_pin}*\n\n"
                    f"Please ensure that you keep your account information secure.\n\n"
                    f"Best Regards,\n"
                    f"*Support Team*"
                ),
            )

            async with httpx.AsyncClient() as client:
                whatsapp_response = await client.post(
                    config.WHATSAPP_API_MESSAGE, json=dict(payload)
                )

            if whatsapp_response.status_code != 200:
                raise ServiceError(
                    detail="Failed to send OTP via WhatsApp.", name="Whatsapp API"
                )

            response.success = True
            response.message = "User successfully changed pin. Account information already sent into phone number."

    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/pin",
    endpoint=change_pin_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user pin endpoint.",
)
