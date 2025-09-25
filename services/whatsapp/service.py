import httpx
from typing import Any, Optional
from utils.logger import logging
from src.schema.payload import SendOTPPayload
from src.secret import WHATSAPP_API_HOST
from services.postgre.connection import async_session, engine
from services.postgre.query import DatabaseQuery
from services.postgre.models import ThirdPartyServiceHistories, Users
from services.postgre.attribute_type import (
    ThirdPartyServiceStatusEnum,
    ThirdPartyServiceTypeEnum,
)


class WhatsAppService:
    async def send_whatsapp(
        self,
        phone_number: str,
        message_template: str,
        ip_address: Optional[str] = None,
        user: Optional[Users] = None,
        user_id: Optional[int] = None,
        **kwargs: Any,
    ):
        if user is not None and user_id is not None:
            raise ValueError(
                "Invalid arguments: both `user` and `user_id` were provided. "
                "Please specify only one to associate the WhatsApp message with a user."
            )

        logging.info("Sending WhatsApp message.")
        message = message_template.format(**kwargs)
        payload = SendOTPPayload(
            phoneNumber=phone_number,
            message=message,
        ).model_dump()

        async with async_session() as session:
            query = DatabaseQuery(session=session)

        async with httpx.AsyncClient() as client:
            response = await client.post(WHATSAPP_API_HOST, json=payload)
            body = response.json()
            history = ThirdPartyServiceHistories(
                users=user,
                user_id=user_id,
                status_code=response.status_code,
                type=ThirdPartyServiceTypeEnum.local_whatsapp_api,
                status=(
                    ThirdPartyServiceStatusEnum.success
                    if response.status_code == 200
                    else ThirdPartyServiceStatusEnum.failed
                ),
                ip_address=ip_address,
                recipient=phone_number,
                response_message=body,
            )
            await query.insert(table=ThirdPartyServiceHistories, data=history)
        await engine.dispose()
