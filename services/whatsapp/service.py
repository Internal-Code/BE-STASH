import httpx
from typing import Any, Optional
from utils.logger import logging
from src.schema.payload import SendOTPPayload
from src.secret import WHATSAPP_API_HOST
from services.postgre.connection import async_session, engine
from services.postgre.query import DatabaseQuery
from services.postgre.models import ThirdPartyServiceHistories
from services.postgre.attribute_type import (
    ThirdPartyServiceStatusEnum,
    ThirdPartyServiceTypeEnum,
)


class WhatsAppService:
    async def send_whatsapp(
        self,
        phone_number: str,
        message_template: str,
        user_id: int,
        ip_address: Optional[str] = None,
        **kwargs: Any,
    ):
        logging.info("Sending WhatsApp message.")
        message = message_template.format(**kwargs)
        payload = SendOTPPayload(
            phoneNumber=phone_number,
            message=message,
        ).model_dump()

        async with httpx.AsyncClient() as client:
            response = await client.post(WHATSAPP_API_HOST, json=payload)
            body = response.json()

            async with async_session() as session:
                query = DatabaseQuery(session=session)
                history = ThirdPartyServiceHistories(
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
