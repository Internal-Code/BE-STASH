from datetime import timedelta
from fastapi import APIRouter, status
from utils.logger import logging
from utils.request_format import UserPin
from src.schema.response import ResponseToken
from utils.validator import check_uuid, check_pin
from utils.database.general import update_user_pin
from utils.forgot_password.general import send_gmail
from src.secret import Config
from utils.jwt.general import (
    get_user,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from utils.custom_error import (
    ServiceError,
    FinanceTrackerApiError,
    MandatoryInputError,
    EntityDoesNotExistError,
    EntityAlreadyFilledError,
)

config = Config()
router = APIRouter(tags=["users-register"], prefix="/users")


async def create_user_pin(pin: UserPin, unique_id: str) -> ResponseToken:
    response = ResponseToken()
    await check_uuid(unique_id=unique_id)
    try:
        account = await get_user(unique_id=unique_id)
        if not account:
            raise EntityDoesNotExistError(detail="Account not found.")

        if account.verified_phone_number is False:
            raise MandatoryInputError(detail="User should validate phone number first.")

        if account.pin:
            raise EntityAlreadyFilledError(detail="Account already filled pin.")

        validated_pin = await check_pin(pin=pin.pin)
        hashed_pin = await get_password_hash(password=validated_pin)
        await update_user_pin(user_uuid=unique_id, pin=hashed_pin)

        if account.verified_email:
            logging.info("Send account information to email.")
            email_body = (
                f"Dear {account.full_name},<br><br>"
                f"We are pleased to inform you that your new account has been successfully created.<br><br>"
                f"You can now log in using the following credentials:<br><br>"
                f"Phone Number: <strong>{account.phone_number}</strong><br>"
                f"PIN: <strong>{validated_pin}</strong><br><br>"
                f"Thank you.<br><br>"
                f"Best regards,<br>"
                f"Support Team"
            )

            await send_gmail(
                email_subject="Success Registered New Finance Tracker Account!",
                email_receiver=account.email,
                email_body=email_body,
            )

        # elif account.verified_phone_number:
        # logging.info("Send account information to phone number.")
        # payload = SendOTPPayload(
        #     phoneNumber=account.phone_number,
        #     message=(
        #         f"Dear *{account.full_name}*,\n\n"
        #         "We are pleased to inform you that your phone number has been successfully verified. "
        #         "You can now log in using the following credentials:\n\n"
        #         f"Phone Number: *{account.phone_number}*\n"
        #         f"PIN: *{validated_pin}*\n\n"
        #         "Please ensure that you keep your account information secure.\n\n"
        #         "Best Regards,\n"
        #         "*Support Team*"
        #     ),
        # )

        # async with httpx.AsyncClient() as client:
        #     whatsapp_response = await client.post(
        #         LOCAL_WHATSAPP_API, json=dict(payload)
        #     )

        # if whatsapp_response.status_code != 200:
        #     raise ServiceError(detail="Failed to send OTP via WhatsApp.", name="Whatsapp API")

        access_token = await create_access_token(
            data={"sub": unique_id},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )
        refresh_token = await create_refresh_token(
            data={"sub": unique_id},
            refresh_token_expires=timedelta(minutes=int(config.REFRESH_TOKEN_EXPIRED)),
        )
        response.access_token = access_token
        response.refresh_token = refresh_token
    except FinanceTrackerApiError as FTE:
        raise FTE
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/create-pin/{unique_id}",
    response_model=ResponseToken,
    endpoint=create_user_pin,
    status_code=status.HTTP_201_CREATED,
    summary="Create user pin.",
)
