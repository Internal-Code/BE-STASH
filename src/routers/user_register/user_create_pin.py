from uuid import UUID
from datetime import timedelta
from src.secret import Config
from src.schema.custom_state import RegisterAccountState
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseToken
from utils.validator import check_security_code
from utils.query.general import find_record, update_record
from services.postgres.models import User
from utils.jwt import get_password_hash, create_access_token
from utils.whatsapp_api import send_account_info_to_phone
from utils.smtp import send_account_info_to_email
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    MandatoryInputError,
    EntityDoesNotExistError,
    EntityAlreadyFilledError,
    DatabaseError,
)

config = Config()
router = APIRouter(tags=["User Register"], prefix="/user/register")


async def create_user_pin(pin: str, unique_id: UUID, db: AsyncSession = Depends(get_db)) -> ResponseToken:
    response = ResponseToken()
    account_record = await find_record(db=db, table=User, column="unique_id", value=str(unique_id))
    validated_pin = check_security_code(type="pin", value=pin)
    hashed_pin = get_password_hash(password=validated_pin)

    try:
        if not account_record:
            raise EntityDoesNotExistError(detail="Account not found.")

        if not account_record.verified_phone_number:
            raise MandatoryInputError(detail="User should validate phone number first.")

        if account_record.pin:
            raise EntityAlreadyFilledError(detail="Account already filled pin.")

        if account_record.verified_email:
            await send_account_info_to_email(
                email=account_record.email,
                full_name=account_record.full_name,
                pin=validated_pin,
                phone_number=account_record.phone_number,
            )

        if account_record.verified_phone_number:
            await send_account_info_to_phone(
                phone_number=account_record.phone_number,
                pin=validated_pin,
                full_name=account_record.full_name,
            )

        await update_record(
            db=db,
            table=User,
            conditions={"unique_id": str(unique_id)},
            data={"pin": hashed_pin, "register_state": RegisterAccountState.SUCCESS},
        )

        access_token = await create_access_token(
            data={"sub": str(unique_id)},
            access_token_expires=timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRED)),
        )
        response.access_token = access_token
    except StashBaseApiError:
        raise
    except ServiceError:
        raise
    except DatabaseError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/create-pin/{unique_id}",
    response_model=ResponseToken,
    endpoint=create_user_pin,
    status_code=status.HTTP_201_CREATED,
    summary="Create user pin.",
)
