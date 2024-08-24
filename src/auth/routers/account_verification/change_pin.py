import httpx
from typing import Annotated
from src.database.models import users, blacklist_tokens
from src.secret import LOCAL_WHATSAPP_API
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.database.connection import database_connection
from fastapi import APIRouter, status, Depends, HTTPException
from src.auth.utils.forgot_password.general import send_gmail
from src.auth.utils.database.general import local_time, check_pin, extract_tokens
from src.auth.utils.request_format import ChangePin, SendOTPPayload
from src.auth.utils.jwt.general import get_current_user, verify_pin, get_password_hash

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pin. Please input valid existing pin.",
            )

        if new_pin != confirmed_pin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new PIN and confirmation PIN do not match. Please ensure both PINs are the same.",
            )

        if duplicated_changed_pin and duplicated_confirmed_pin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="New PIN cannot be the same as the current PIN. Please choose a different PIN.",
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
            except HTTPException as E:
                raise E
            except Exception as E:
                logging.error(f"Error while change_pin_endpoint: {E}.")
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal Server Error: {E}.",
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
                f"<strong>The Support Team</strong>"
            )

            await send_gmail(
                email_subject="Registered New Finance Tracker Account.",
                email_receiver=current_user.email,
                email_body=email_body,
            )

            response.success = True
            response.message = "User successfully changed pin. Account information already sent into email."

        if current_user.verified_phone_number:
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
                    LOCAL_WHATSAPP_API, json=dict(payload)
                )

            if whatsapp_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send OTP via WhatsApp.",
                )
            response.success = True
            response.message = "User successfully changed pin. Account information already sent into phone number."

    except HTTPException as e:
        raise e

    except Exception as E:
        logging.error(f"Error after change_pin_endpoint: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/pin",
    endpoint=change_pin_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user pin endpoint.",
)