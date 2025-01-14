from utils.helper import local_time
from fastapi import APIRouter, status, Depends
from src.schema.request_format import UserEmail
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from services.postgres.models import User, ResetPin
from src.schema.response import ResponseDefault, UserStatus
from src.schema.validator import PhoneNumberValidatorMixin
from utils.query.general import find_record, insert_record, update_record
from utils.custom_error import (
    DataNotFoundError,
    ServiceError,
    StashBaseApiError,
    InvalidOperationError,
)

router = APIRouter(tags=["User Reset Account"], prefix="/user/reset-account")


async def user_endpoint(
    identifier: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()

    query = {}

    try:
        if identifier.isdigit():
            validated_phone_number = PhoneNumberValidatorMixin.validate_phone_number(phone_number=identifier)
            query["phone_number"] = validated_phone_number
        elif "@" in identifier:
            validated_email = UserEmail(email=identifier)
            query["email"] = validated_email.email
        else:
            raise InvalidOperationError("Should be a valid phone number or email.")

        account_record = await find_record(db=db, table=User, **query)

        if not account_record:
            raise DataNotFoundError(detail="User not found.")

        reset_pin_record = await find_record(db=db, table=ResetPin, unique_id=account_record.unique_id)
        updated_query = {**query, "save_to_hit_at": current_time, "unique_id": account_record.unique_id}

        if not reset_pin_record:
            await insert_record(db=db, table=ResetPin, data=updated_query)
        else:
            updated_query = {**updated_query, "updated_at": current_time}
            await update_record(
                db=db, table=ResetPin, conditions={"unique_id": account_record.unique_id}, data=updated_query
            )

        response.message = "User found."
        response.data = UserStatus(
            unique_id=account_record.unique_id,
            register_status=account_record.register_state,
            verified_email=account_record.verified_email,
            verified_phone_number=account_record.verified_phone_number,
        )

    except StashBaseApiError:
        raise
    except Exception as e:
        raise ServiceError(detail=f"Service error: {e}.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/{identifier}",
    response_model=ResponseDefault,
    endpoint=user_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get unique id user.",
)
