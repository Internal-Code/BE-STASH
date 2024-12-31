import httpx
from pytz import timezone
from fastapi import APIRouter, status
from datetime import datetime, timedelta
from src.secret import Config
from utils.logger import logging
from utils.validator import check_uuid
from utils.jwt.general import get_user
from src.schema.response import ResponseDefault, UniqueID
from utils.forgot_password.general import send_gmail
from utils.request_format import SendVerificationLink, SendOTPPayload
from utils.custom_error import (
    ServiceError,
    FinanceTrackerApiError,
    MandatoryInputError,
    EntityDoesNotExistError,
    InvalidOperationError,
)
from utils.database.general import (
    save_reset_pin_data,
    extract_reset_pin_data,
)

config = Config()
router = APIRouter(tags=["User Reset Account"], prefix="/user/reset-account")


async def send_reset_link_endpoint(
    unique_id: str, schema: SendVerificationLink
) -> ResponseDefault:
    response = ResponseDefault()
    await check_uuid(unique_id=unique_id)

    try:
        account = await get_user(unique_id=unique_id)

        if not account:
            raise EntityDoesNotExistError(detail="Account not found.")

        reset_link = f"http://localhost:8000/api/v1/users/reset-pin/{unique_id}"

        if schema.method == schema.method.EMAIL:
            if not account.verified_email and account.email:
                logging.info("User email is not verified.")
                raise InvalidOperationError(
                    detail="User email should be verified to send otp."
                )

            if not account.email:
                logging.info("User is not input email yet.")
                raise MandatoryInputError(detail="User should add email first.")

            if not account.pin:
                logging.info("User is not created pin.")
                raise MandatoryInputError(detail="User should create pin first.")

            if account.verified_email:
                logging.info("User account email validated.")

                email_body = (
                    f"Dear {account.email},<br><br>"
                    f"We received a request to reset your password. Please click the link below to create a new password:<br><br>"
                    f'<a href="{reset_link}">Reset Password</a><br><br>'
                    f"Please note, this password reset link is only valid for <b>5 minutes</b>. If you did not request a password reset, please ignore this email.<br>"
                    f"Thank you,<br><br>"
                    f"Best regards,<br>"
                    f"<b>Support Team</b>"
                )

                latest_reset_pin_data = await extract_reset_pin_data(
                    user_uuid=unique_id
                )

                if not latest_reset_pin_data:
                    logging.info("Initialized send reset password link via email.")

                    await save_reset_pin_data(user_uuid=unique_id, email=account.email)

                    await send_gmail(
                        email_subject="Reset Password",
                        email_receiver=account.email,
                        email_body=email_body,
                    )

                    response.success = True
                    response.message = "Password reset link sent to email."
                    response.data = UniqueID(unique_id=unique_id)

                now_utc = datetime.now(timezone("UTC"))
                jakarta_timezone = timezone("Asia/Jakarta")
                blacklist_time = now_utc + timedelta(minutes=1)
                if (
                    latest_reset_pin_data is None
                    or latest_reset_pin_data.save_to_hit_at is None
                ):
                    valid_blacklist_time = blacklist_time
                else:
                    valid_blacklist_time = latest_reset_pin_data.save_to_hit_at
                times_later_jakarta = valid_blacklist_time.astimezone(jakarta_timezone)
                formatted_time = times_later_jakarta.strftime("%Y-%m-%d %H:%M:%S")

                if latest_reset_pin_data is not None and now_utc < valid_blacklist_time:
                    logging.info("User should wait API cooldown.")
                    raise InvalidOperationError(
                        detail=f"Should wait until {formatted_time}."
                    )

                if now_utc >= valid_blacklist_time:
                    logging.info("Saved new reset pin request data.")

                    await send_gmail(
                        email_subject="Reset Password",
                        email_receiver=account.email,
                        email_body=email_body,
                    )

                    response.success = True
                    response.message = "Password reset link sent to email."
                    response.data = UniqueID(unique_id=unique_id)

                return response
            return response

        if schema.method == schema.method.PHONE_NUMBER:
            if not account.pin:
                logging.info("User is not created pin.")
                raise MandatoryInputError(
                    detail="User should create pin first.",
                )

            if account.phone_number and not account.verified_phone_number:
                logging.info("User phone number not verified.")
                raise InvalidOperationError(
                    detail="User phone number should be verified first to send otp",
                )

            if not account.phone_number:
                logging.info("User phone number empty.")
                raise InvalidOperationError(detail="User is not added phone number.")

            if account.verified_phone_number is True:
                logging.info("User phone number validated.")

                payload = SendOTPPayload(
                    phoneNumber=account.phone_number,
                    message=(
                        f"Dear *{account.full_name}*,\n\n"
                        f"We received a request to reset your password. Please click the link below to create a new password:\n\n"
                        f"{reset_link}\n\n"
                        f"Please note, this password reset link is only valid for *5 minutes*. If you did not request a password reset, please ignore this message.\n\n"
                        f"Thank you,\n\n"
                        f"Best regards,\n"
                        "*Support Team*"
                    ),
                )

                latest_reset_pin_data = await extract_reset_pin_data(
                    user_uuid=unique_id
                )

                if not latest_reset_pin_data:
                    logging.info(
                        "Initialized send reset password link via phone nnumber."
                    )

                    await save_reset_pin_data(user_uuid=unique_id, email=account.email)

                    async with httpx.AsyncClient() as client:
                        whatsapp_response = await client.post(
                            config.WHATSAPP_API_MESSAGE, json=dict(payload)
                        )

                    if whatsapp_response.status_code != 200:
                        raise ServiceError(
                            detail="Failed to send OTP via WhatsApp.",
                            name="Whatsapp API",
                        )

                    response.success = True
                    response.message = "Password reset link sent to phone number."
                    response.data = UniqueID(unique_id=unique_id)

                now_utc = datetime.now(timezone("UTC"))
                jakarta_timezone = timezone("Asia/Jakarta")
                blacklist_time = now_utc + timedelta(minutes=1)
                if (
                    latest_reset_pin_data is None
                    or latest_reset_pin_data.save_to_hit_at is None
                ):
                    valid_blacklist_time = blacklist_time
                else:
                    valid_blacklist_time = latest_reset_pin_data.save_to_hit_at
                times_later_jakarta = valid_blacklist_time.astimezone(jakarta_timezone)
                formatted_time = times_later_jakarta.strftime("%Y-%m-%d %H:%M:%S")

                if latest_reset_pin_data is not None and now_utc < valid_blacklist_time:
                    logging.info("User should wait API cooldown.")
                    raise InvalidOperationError(
                        detail=f"Should wait until {formatted_time}."
                    )

                if now_utc >= valid_blacklist_time:
                    logging.info("Saved new reset pin request data.")

                    await save_reset_pin_data(user_uuid=unique_id, email=account.email)

                    async with httpx.AsyncClient() as client:
                        whatsapp_response = await client.post(
                            config.WHATSAPP_API_CONNECTION, json=dict(payload)
                        )

                    if whatsapp_response.status_code != 200:
                        raise ServiceError(
                            detail="Failed to send OTP via WhatsApp.",
                            name="Whatsapp API",
                        )

                    response.success = True
                    response.message = "Password reset link sent to phone number."
                    response.data = UniqueID(unique_id=unique_id)

                return response
            return response
    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")


router.add_api_route(
    methods=["POST"],
    path="/send-link/{unique_id}",
    response_model=ResponseDefault,
    endpoint=send_reset_link_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send forgot pin reset link.",
)
