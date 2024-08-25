import httpx
from pytz import timezone
from datetime import datetime, timedelta
from src.secret import LOCAL_WHATSAPP_API
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault, UniqueID
from src.auth.utils.request_format import SendVerificationLink, SendOTPPayload
from src.auth.utils.forgot_password.general import send_gmail
from src.auth.utils.jwt.general import get_user
from fastapi import APIRouter, HTTPException, status
from src.auth.utils.database.general import (
    save_reset_pin_data,
    extract_reset_pin_data,
    verify_uuid,
)

router = APIRouter(tags=["users-forgot-pin"], prefix="/users")


async def send_reset_link_endpoint(
    unique_id: str, schema: SendVerificationLink
) -> ResponseDefault:
    response = ResponseDefault()
    await verify_uuid(unique_id=unique_id)

    try:
        account = await get_user(unique_id=unique_id)

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        reset_link = f"http://localhost:8000/api/v1/users/reset-pin/{unique_id}"

        if schema.method == schema.method.EMAIL:
            if not account.verified_email and account.email:
                logging.info("User email is not verified.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User email is not verified.",
                )

            if not account.email:
                logging.info("User is not input email yet.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User should add email first.",
                )

            if not account.pin:
                logging.info("User is not created pin.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not created account pin.",
                )

            if account.verified_email:
                logging.info("User account email validated.")

                email_body = (
                    f"Dear {account.email},<br><br>"
                    f"We received a request to reset your password. Please click the link below to create a new password:<br><br>"
                    f'<a href="{reset_link}">Reset Password</a><br><br>'
                    f"Please note, this password reset link is only valid for <b>5 minutes</b>. If you did not request a password reset, please ignore this email.<br><br>"
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
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Should wait until {formatted_time}.",
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
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not created account pin.",
                )

            if account.phone_number and not account.verified_phone_number:
                logging.info("User phone number not verified.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User phone number not verified",
                )

            if not account.phone_number:
                logging.info("User phone number empty.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not added phone number.",
                )

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
                            LOCAL_WHATSAPP_API, json=dict(payload)
                        )

                    if whatsapp_response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to send OTP via WhatsApp.",
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
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Should wait until {formatted_time}.",
                    )

                if now_utc >= valid_blacklist_time:
                    logging.info("Saved new reset pin request data.")

                    await save_reset_pin_data(user_uuid=unique_id, email=account.email)

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
                    response.message = "Password reset link sent to phone number."
                    response.data = UniqueID(unique_id=unique_id)

                return response
            return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Server error send reset link: {e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}.",
        )


router.add_api_route(
    methods=["POST"],
    path="/send-reset-link/{unique_id}",
    response_model=ResponseDefault,
    endpoint=send_reset_link_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Send forgot pin reset link.",
)
