from uuid import uuid4
from datetime import timedelta
from utils.logger import logging
from utils.helper import local_time
from src.schema.request_format import CreateUser
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from services.postgres.models import User, SendOtp
from utils.query.general import find_record, insert_record
from src.schema.validator import PhoneNumberValidatorMixin
from utils.whatsapp_api import send_otp_whatsapp
from utils.generator import random_number
from src.schema.response import ResponseDefault, UniqueId
from utils.custom_error import ServiceError, DatabaseQueryError, StashBaseApiError, EntityAlreadyExistError

router = APIRouter(tags=["User Register"], prefix="/user/register")


async def register_user(schema: CreateUser, db: AsyncSession = Depends(get_db)) -> ResponseDefault:
    unique_id = str(uuid4())
    generated_otp = str(random_number(6))
    response = ResponseDefault()
    validated_phone_number = PhoneNumberValidatorMixin.validate_phone_number(phone_number=schema.phone_number)
    phone_number_record = await find_record(db=db, table=User, phone_number=validated_phone_number)
    email_record = await find_record(db=db, table=User, email=schema.email)

    try:
        if phone_number_record:
            raise EntityAlreadyExistError(detail="Phone number already registered.")

        if email_record:
            raise EntityAlreadyExistError(detail="Email already registered.")

        await insert_record(
            db=db,
            table=User,
            data={
                "unique_id": unique_id,
                "full_name": schema.full_name,
                "phone_number": schema.phone_number,
                "email": schema.email,
            },
        )

        logging.info("Inserting user otp entry.")
        await insert_record(
            db=db,
            table=SendOtp,
            data={
                "unique_id": unique_id,
                "otp_number": generated_otp,
                "save_to_hit_at": local_time(),
                "blacklisted_at": local_time() + timedelta(minutes=3),
            },
        )

        logging.info("Sending OTP code.")
        tes = await send_otp_whatsapp(phone_number=validated_phone_number, generated_otp=generated_otp)
        logging.info(tes)

        response.success = True
        response.message = "Account successfully created."
        response.data = UniqueId(unique_id=unique_id)
    except StashBaseApiError:
        raise
    except DatabaseQueryError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")
    return response


router.add_api_route(
    methods=["POST"],
    path="/new-account",
    response_model=ResponseDefault,
    endpoint=register_user,
    status_code=status.HTTP_201_CREATED,
    summary="Account registration.",
)
