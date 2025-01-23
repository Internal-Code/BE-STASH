from utils.query import QueryDatabase
from services.postgres.models import User
from src.schema.request_format import UserEmail
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.response import ResponseDefault, UserStatus
from src.schema.validator import PhoneNumberValidatorMixin
from utils.error import (
    DataNotFoundError,
    ServiceError,
    StashBaseApiError,
    InvalidOperationError,
)

router = APIRouter(tags=["User General"], prefix="/user/general")


async def get_user_endpoint(
    identifier: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)

    filter = {}

    try:
        if identifier.isdigit():
            validated_phone_number = PhoneNumberValidatorMixin.validate_phone_number(
                phone_number=identifier
            )
            filter["phone_number"] = validated_phone_number
        elif "@" in identifier:
            try:
                validated_email = UserEmail(email=identifier)  # Validate email format
                filter["email"] = validated_email.email
            except ValueError:
                raise InvalidOperationError("Email should be in a proper format.")
        else:
            raise InvalidOperationError("Should be a valid phone number or email.")

        account_record = await query.find(table=User, **filter)

        if not account_record:
            raise DataNotFoundError(detail="User not found.")

        response.message = "User found."
        response.data = UserStatus(
            unique_id=account_record.unique_id,
            register_state=account_record.register_state,
            otp_state=account_record.otp_state,
            is_email_verified=account_record.verified_email,
            is_phone_number_verified=account_record.verified_phone_number,
        )

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/get-user/{identifier}",
    response_model=ResponseDefault,
    endpoint=get_user_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get unique id user.",
)
