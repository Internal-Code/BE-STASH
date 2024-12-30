import httpx
from pytz import timezone
from datetime import datetime
from fastapi import APIRouter, status
from src.secret import Config
from src.schema.response import ResponseDefault
from utils.validator import check_uuid, check_pin
from utils.request_format import ForgotPin, SendOTPPayload
from utils.jwt.general import get_user, get_password_hash
from utils.database.general import extract_reset_pin_data, reset_user_pin
from utils.custom_error import (
    ServiceError,
    FinanceTrackerApiError,
    EntityDoesNotMatchedError,
    EntityDoesNotExistError,
    InvalidOperationError,
)

config = Config()
router = APIRouter(tags=["users-forgot-pin"], prefix="/users")


async def reset_password(schema: ForgotPin, unique_id: str) -> ResponseDefault:
    response = ResponseDefault()
    await check_uuid(unique_id=unique_id)
    try:
        account = await get_user(unique_id=unique_id)

        latest_data = await extract_reset_pin_data(user_uuid=unique_id)
        if not latest_data:
            raise EntityDoesNotExistError(detail="User not found.")

        now_utc = datetime.now(timezone("UTC"))

        if now_utc > latest_data.blacklisted_at:
            raise InvalidOperationError(detail="Reset pin token expired.")

        if now_utc < latest_data.blacklisted_at:
            validated_pin = await check_pin(pin=schema.pin)

            if schema.pin != schema.confirm_new_pin:
                raise EntityDoesNotMatchedError(
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
                        config.WHATSAPP_API_MESSAGE, json=dict(payload)
                    )

                if whatsapp_response.status_code != 200:
                    raise ServiceError(
                        detail="Failed to send OTP via WhatsApp.", name="Whatsapp API"
                    )

                response.success = True
                response.message = "Pin successfully reset."

    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/reset-pin/{unique_id}",
    response_model=ResponseDefault,
    endpoint=reset_password,
    status_code=status.HTTP_200_OK,
    summary="Create new pin from forgot pin endpoint.",
)
