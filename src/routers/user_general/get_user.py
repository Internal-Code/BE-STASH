from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.query.general import find_record
from services.postgres.models import User
from src.schema.request_format import UserEmail
from src.schema.response import ResponseDefault, UserStatus
from src.schema.validator import PhoneNumberValidatorMixin
from utils.custom_error import (
    DataNotFoundError,
    ServiceError,
    StashBaseApiError,
    InvalidOperationError,
)

router = APIRouter(tags=["User General"], prefix="/user/general")


async def user_endpoint(
    identifier: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()

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

        response.message = "User found."
        response.data = UserStatus(unique_id=account_record.unique_id, register_status=account_record.register_state)

    except StashBaseApiError:
        raise
    except Exception as e:
        raise ServiceError(detail=f"Service error: {e}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["GET"],
    path="/get-user",
    response_model=ResponseDefault,
    endpoint=user_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get unique id user.",
)
