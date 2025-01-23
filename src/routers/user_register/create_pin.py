from uuid import UUID
from src.secret import Config
from datetime import timedelta
from utils.jwt import JWTHandler
from utils.query import QueryDatabase
from services.postgres.models import User
from utils.whatsapp_api import send_whatsapp
from src.schema.request_format import UserPin
from src.schema.response import ResponseToken
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.custom_state import RegisterAccountState
from fastapi import APIRouter, status, Depends, BackgroundTasks
from utils.error import (
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
    DataNotFoundError,
    EntityAlreadyFilledError,
)

config = Config()
jwt_handler = JWTHandler(config)
router = APIRouter(tags=["User Register"], prefix="/user/register")


async def create_pin_endpoint(
    schema: UserPin,
    unique_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResponseToken:
    response = ResponseToken()
    query = QueryDatabase(db)
    account_record = await query.find(table=User, unique_id=str(unique_id))
    hashed_pin = jwt_handler.get_password_hash(password=schema.pin)

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
                    f"Dear *{account_record.full_name}*,\n\n"
                    "We are pleased to inform you that your new account has been successfully registered. "
                    "You can now log in using the following credentials:\n\n"
                    f"Phone Number: *{account_record.phone_number}*\n"
                    f"PIN: *{schema.pin}*\n\n"
                    "Please ensure that you keep your account information secure.\n\n"
                    "Best Regards,\n"
                    "STASH Support Team"
                ),
                pin=schema.pin,
                full_name=account_record.full_name,
            )

        await query.update(
            table=User,
            condition={"unique_id": str(unique_id)},
            data={"pin": hashed_pin, "register_state": RegisterAccountState.SUCCESS},
        )

        access_token = jwt_handler.create_access_token(
            data={"sub": str(unique_id)},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )

        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": str(unique_id)},
            refresh_token_expires=timedelta(minutes=int(config.REFRESH_TOKEN_EXPIRED)),
        )

        response.access_token = access_token
        response.refresh_token = refresh_token

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/create-pin/{unique_id}",
    response_model=ResponseToken,
    endpoint=create_pin_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create user pin.",
)
