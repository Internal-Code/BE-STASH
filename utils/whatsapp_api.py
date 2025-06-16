import httpx
from src.secret import WHATSAPP_API_MESSAGE
from utils.logger import logging
from src.schema.request_format import SendOTPPayload
from errors.custom_error import ServiceError


async def send_whatsapp(phone_number: str, message_template: str, **kwargs) -> None:
    logging.info("Sending WhatsApp message.")
    message = message_template.format(**kwargs)

    payload = SendOTPPayload(
        phoneNumber=phone_number,
        message=message,
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(WHATSAPP_API_MESSAGE, json=dict(payload))
        if response.status_code != 200:
            raise ServiceError(
                "Failed to send WhatsApp message.", {"WhatsApp API": "pass error here"}
            )
    except Exception:
        raise ServiceError(
            "Failed to send WhatsApp message.", {"WhatsApp API": "pass error here"}
        )
    return None
