import httpx
from src.secret import Config
from utils.logger import logging
from src.schema.request_format import SendOTPPayload
from utils.custom_error import ServiceError

config = Config()


async def send_otp_whatsapp(phone_number: str, generated_otp: str) -> None:
    payload = SendOTPPayload(
        phoneNumber=phone_number,
        message=f"""Your verification code is *{generated_otp}*. Please enter this code to complete your verification. Kindly note that this code will *expire in 3 minutes*.""",
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(config.WHATSAPP_API_MESSAGE, json=dict(payload))

        if response.status_code != 200:
            raise ServiceError(detail="Failed to send OTP via WhatsApp.", name="Whatsapp API")

    except Exception:
        raise ServiceError(detail="Whatsapp API error.", name="Whatsapp API")
    finally:
        await client.aclose()


async def send_account_info_to_phone(full_name: str, phone_number: str, pin: str) -> None:
    logging.info("Send account information to phone number.")
    payload = SendOTPPayload(
        phoneNumber=phone_number,
        message=(
            f"Dear *{full_name}*,\n\n"
            "We are pleased to inform you that your new account has been successfully registered. "
            "You can now log in using the following credentials:\n\n"
            f"Phone Number: *{phone_number}*\n"
            f"PIN: *{pin}*\n\n"
            "Please ensure that you keep your account information secure.\n\n"
            "Best Regards,\n"
            "STASH Support Team"
        ),
    )

    try:
        async with httpx.AsyncClient() as client:
            await client.post(config.WHATSAPP_API_MESSAGE, json=dict(payload))
    except Exception:
        raise ServiceError(detail="Failed to send accouunt info via WhatsApp.", name="Whatsapp API")
