from uuid import UUID
from src.secret import Config
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, BackgroundTasks
from src.schema.request_format import ResetPinRequest
from utils.helper import local_time
from services.postgres.models import User, UserToken, ResetPin
from utils.query.general import update_record, find_record, insert_record
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    InvalidOperationError
)

config = Config()
router = APIRouter(tags=["User Reset Account"], prefix="/user/reset-account")


async def reset_password(
    schema: ResetPinRequest,
    unique_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    
    current_time = local_time()
    
    account_record = await find_record(db=db, table=User, unique_id=str(unique_id))
    reset_pin_record = await find_record(db=db, table=ResetPin, unique_id=account_record.unique_id)
    
    try:
        if not account_record:
            raise DataNotFoundError(detail="User not found.")
        
        if current_time > reset_pin_record.blacklisted_at:
            raise InvalidOperationError(detail="Reset pin token expired.")
        
        # TODO: should refactor this endpoint
        pass
        # account = await get_user(unique_id=unique_id)

        # latest_data = await extract_reset_pin_data(user_uuid=unique_id)

        # now_utc = datetime.now(timezone("UTC"))

        # if now_utc > latest_data.blacklisted_at:
        #     raise InvalidOperationError(detail="Reset pin token expired.")

        # if now_utc < latest_data.blacklisted_at:
        #     validated_pin = check_security_code(type="pin", pin=schema.pin)

        #     if schema.pin != schema.confirm_new_pin:
        #         raise EntityDoesNotMatchedError(
        #             detail="Passwords is not match.",
        #         )

        #     if schema.pin == schema.confirm_new_pin:
        #         payload = SendOTPPayload(
        #             phoneNumber=account.phone_number,
        #             message=(
        #                 f"Dear *{account.full_name}*,\n\n"
        #                 f"We would like to inform you that your PIN has been successfully changed.\n\n"
        #                 f"Please use the following details to log in to your account:\n\n"
        #                 f"Phone Number: *{account.phone_number}*\n"
        #                 f"New PIN: *{validated_pin}*\n\n"
        #                 f"For your security, please ensure you keep this information confidential.\n\n"
        #                 f"Should you have any questions or require further assistance, feel free to contact our support team.\n\n"
        #                 f"Best regards,\n"
        #                 f"*Support Team*"
        #             ),
        #         )

        #         hashed_pin = await get_password_hash(password=schema.pin)
        #         await reset_user_pin(user_uuid=unique_id, changed_pin=hashed_pin)

        #         async with httpx.AsyncClient() as client:
        #             whatsapp_response = await client.post(
        #                 config.WHATSAPP_API_MESSAGE, json=dict(payload)
        #             )

        #         if whatsapp_response.status_code != 200:
        #             raise ServiceError(
        #                 detail="Failed to send OTP via WhatsApp.", name="Whatsapp API"
        #             )

        #         response.success = True
        #         response.message = "Pin successfully reset."

    except StashBaseApiError:
        raise

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/reset-pin/{unique_id}",
    response_model=ResponseDefault,
    endpoint=reset_password,
    status_code=status.HTTP_200_OK,
    summary="Create new pin from forgot pin endpoint.",
)
