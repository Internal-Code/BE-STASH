import httpx
from src.secret import Config
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
            await client.post(config.WHATSAPP_API_MESSAGE, json=dict(payload))
    except Exception:
        raise ServiceError(detail="Failed to send OTP via WhatsApp.", name="Whatsapp API")
