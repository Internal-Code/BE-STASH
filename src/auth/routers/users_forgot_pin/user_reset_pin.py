import httpx
from src.secret import LOCAL_WHATSAPP_API
from datetime import datetime
from pytz import timezone
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import ForgotPin, SendOTPPayload
from fastapi import APIRouter, HTTPException, status
from src.auth.utils.database.general import (
    extract_reset_pin_data,
    verify_uuid,
    reset_user_pin,
    check_pin,
)
from src.auth.utils.jwt.general import get_user, get_password_hash

router = APIRouter(tags=["users-forgot-pin"], prefix="/users")


async def reset_password(schema: ForgotPin, unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)
    try:
        account = await get_user(unique_id=unique_id)

        latest_data = await extract_reset_pin_data(user_uuid=unique_id)
        if not latest_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        now_utc = datetime.now(timezone("UTC"))

        if now_utc > latest_data.blacklisted_at:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Reset pin token expired."
            )

        if now_utc < latest_data.blacklisted_at:
            validated_pin = await check_pin(pin=schema.pin)

            if schema.pin != schema.confirm_new_pin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Passwords is not match.",
                )

            if schema.pin == schema.confirm_new_pin:
                payload = SendOTPPayload(
                    phoneNumber=account.phone_number,
                    message=(
                        f"Dear *{account.full_name}*,\n\n"
                        f"We would like to inform you that your PIN has been successfully changed.\n\n"
                        f"Please use the following details to log in to your account:\n\n"
                        f"Phone Number: *{account.phone_number}*\n"
                        f"New PIN: *{validated_pin}*\n\n"
                        f"For your security, please ensure you keep this information confidential.\n\n"
                        f"Should you have any questions or require further assistance, feel free to contact our support team.\n\n"
                        f"Best regards,\n"
                        f"*Support Team*"
                    ),
                )

                hashed_pin = await get_password_hash(password=schema.pin)
                await reset_user_pin(user_uuid=unique_id, changed_pin=hashed_pin)

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
                response.message = "Pin successfully reset."

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Server error resetting password: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/reset-pin/{unique_id}",
    response_model=ResponseDefault,
    endpoint=reset_password,
    status_code=status.HTTP_200_OK,
    summary="Create new pin from forgot pin endpoint.",
)
