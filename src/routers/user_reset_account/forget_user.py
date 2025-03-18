from utils.helper import local_time
from utils.query import QueryDatabase
from services.postgres.models import User
from src.schema.request_format import Email
from services.postgres.models import ResetPin
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

router = APIRouter(tags=["User Reset Account"], prefix="/user/reset-account")


async def forget_user_endpoint(
    identifier: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)

    current_time = local_time()

    filter = {}

    try:
        if identifier.isdigit():
            validated_phone_number = PhoneNumberValidatorMixin.validate_phone_number(
                phone_number=identifier
            )
            filter["phone_number"] = validated_phone_number
        elif "@" in identifier:
            try:
                validated_email = Email(email=identifier)  # Validate email format
                filter["email"] = validated_email.email
            except ValueError:
                raise InvalidOperationError("Email should be in a proper format.")
        else:
            raise InvalidOperationError("Should be a valid phone number or email.")

        account_record = await query.find(table=User, **filter)

        if not account_record:
            raise DataNotFoundError(detail="User not found.")

        await query.insert(
            table=ResetPin,
            data={
                "unique_id": account_record.unique_id,
                "created_at": current_time,
                "phone_number": account_record.phone_number,
                "email": account_record.email,
                "save_to_hit_at": current_time,
                "blacklisted_at": current_time,
            },
        )

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
    methods=["POST"],
    path="/forget-user/{identifier}",
    response_model=ResponseDefault,
    endpoint=forget_user_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get unique id user.",
)
