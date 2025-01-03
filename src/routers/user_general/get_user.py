from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.query.general import find_record
from services.postgres.models import User
from utils.validator import check_phone_number
from src.schema.response import ResponseDefault, UserStatus
from utils.custom_error import (
    EntityDoesNotExistError,
    ServiceError,
    StashBaseApiError,
    DatabaseError,
)

router = APIRouter(tags=["User General"], prefix="/user/general")


async def get_user_endpoint(phone_number: str, db: AsyncSession = Depends(get_db)) -> ResponseDefault:
    response = ResponseDefault()
    validated_phone_number = check_phone_number(phone_number=phone_number)
    account_record = await find_record(db=db, table=User, phone_number=validated_phone_number)

    try:
        if not account_record:
            raise EntityDoesNotExistError(detail="User not found.")

        response.success = True
        response.message = "User found."
        response.data = UserStatus(unique_id=account_record.unique_id, register_status=account_record.register_state)

    except StashBaseApiError:
        raise

    except DatabaseError:
        raise

    except Exception as e:
        raise ServiceError(detail=f"Service error: {e}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["GET"],
    path="/get-user",
    response_model=ResponseDefault,
    endpoint=get_user_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Get unique id user.",
)
