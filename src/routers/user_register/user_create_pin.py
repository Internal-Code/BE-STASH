from uuid import UUID
from datetime import timedelta
from src.secret import Config
from src.schema.custom_state import RegisterAccountState
from fastapi import APIRouter, status, Depends, BackgroundTasks
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseToken
from utils.query.general import find_record, update_record
from services.postgres.models import User
from utils.jwt import get_password_hash, create_access_token
from utils.whatsapp_api import send_whatsapp
from src.schema.request_format import UserPin
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
    DataNotFoundError,
    EntityAlreadyFilledError,
)

config = Config()
router = APIRouter(tags=["User Register"], prefix="/user/register")


async def create_pin_endpoint(
    schema: UserPin, unique_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> ResponseToken:
    response = ResponseToken()
    account_record = await find_record(db=db, table=User, unique_id=str(unique_id))
    hashed_pin = get_password_hash(password=schema.pin)

    try:
        if not account_record:
            raise DataNotFoundError(detail="Account not found.")

        if account_record.register_state == RegisterAccountState.SUCCESS:
            raise EntityAlreadyFilledError(detail="Account already set pin.")

        if not account_record.verified_phone_number:
            raise MandatoryInputError(detail="Should validate phone number first.")

        if account_record.verified_phone_number:
            background_tasks.add_task(
                send_whatsapp,
                phone_number=account_record.phone_number,
                message_template=(
                    "Dear *{full_name}*,\n\n"
                    "We are pleased to inform you that your new account has been successfully registered. "
                    "You can now log in using the following credentials:\n\n"
                    "Phone Number: *{phone_number}*\n"
                    "PIN: *{pin}*\n\n"
                    "Please ensure that you keep your account information secure.\n\n"
                    "Best Regards,\n"
                    "STASH Support Team"
                ),
                pin=schema.pin,
                full_name=account_record.full_name,
            )

        await update_record(
            db=db,
            table=User,
            conditions={"unique_id": str(unique_id)},
            data={"pin": hashed_pin, "register_state": RegisterAccountState.SUCCESS},
        )

        access_token = create_access_token(
            data={"sub": str(unique_id)},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )
        response.access_token = access_token

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/create-pin/{unique_id}",
    response_model=ResponseToken,
    endpoint=create_pin_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create user pin.",
)
