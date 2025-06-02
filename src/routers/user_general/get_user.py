from utils.logger import logging
from utils.query import QueryDatabase
from services.postgre.model import User
from src.schema.request_format import Email
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from src.schema.response import ResponseDefault, UserInfoResponse
from src.schema.validator import PhoneNumberValidatorMixin
from utils.error import (
    DataNotFoundError,
    ServiceError,
    StashBaseApiError,
    InvalidOperationError,
)

router = APIRouter(tags=["User General"], prefix="/user/general")


async def get_user_endpoint(
    identifier: str, db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    logging.info("Get user endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    user_info_response = UserInfoResponse()
    filter = {}
    try:
        if identifier.isdigit():
            logging.info("Phone number detected.")
            validated_phone_number = PhoneNumberValidatorMixin.validate_phone_number(
                phone_number=identifier
            )
            filter["phone_number"] = validated_phone_number
        elif "@" in identifier:
            logging.info("Email detected.")
            try:
                validated_email = Email(email=identifier)
                filter["email"] = validated_email.email
            except ValueError:
                logging.error("Invalid email format.")
                raise InvalidOperationError("Email should be in a proper format.")
        else:
            logging.error("Identifier should be valid phone number or valid email.")
            raise InvalidOperationError("Should be a valid phone number or email.")

        account_record = await query.find(table=User, **filter)

        if not account_record:
            logging.error("User not found.")
            raise DataNotFoundError(detail="User not found.")

        user_info_response.unique_id = account_record.unique_id
        user_info_response.register_state = account_record.register_state
        user_info_response.otp_state = account_record.otp_state
        user_info_response.is_email_verified = account_record.verified_email
        user_info_response.is_phone_number_verified = (
            account_record.verified_phone_number
        )

        response.message = "User info successfully fetched."
        response.data = user_info_response.model_dump()

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
