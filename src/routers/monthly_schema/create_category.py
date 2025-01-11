from uuid import UUID
from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import CategorySchema, MonthlySchema, UserToken, BlacklistToken
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from src.schema.request_format import MonthlyCategory
from utils.query.general import insert_record, find_record
from utils.custom_error import (
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    InvalidTokenError,
)

router = APIRouter(tags=["Monthly Schema"])


async def create_category_endpoint(
    schema: MonthlyCategory,
    month_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    category_record = await find_record(
        db=db,
        table=CategorySchema,
        unique_id=current_user.unique_id,
        category=schema.category,
        category_id=str(month_id),
        deleted_at=None,
    )
    monthly_schema_record = await find_record(db=db, table=MonthlySchema, month_id=str(month_id))
    user_token_record = await find_record(db=db, table=UserToken, unique_id=current_user.unique_id)
    blacklist_access_token = await find_record(db=db, table=BlacklistToken, access_token=user_token_record.access_token)
    blacklist_refresh_token = await find_record(
        db=db, table=BlacklistToken, refresh_token=user_token_record.refresh_token
    )
    print(blacklist_access_token)

    try:
        if blacklist_access_token:
            raise InvalidTokenError(detail="Access token already blacklisted.")

        if blacklist_refresh_token:
            raise InvalidTokenError(detail="Refresh token already blacklisted.")

        if not monthly_schema_record:
            raise DataNotFoundError(detail="Schema not found.")

        if category_record:
            logging.info(f"Category {schema.category} already created.")
            raise EntityAlreadyExistError(detail=f"Category {schema.category} already created.")

        await insert_record(
            db=db,
            table=CategorySchema,
            data={
                "category": schema.category,
                "budget": schema.budget,
                "category_id": str(month_id),
                "unique_id": current_user.unique_id,
            },
        )
        response.message = "Created new category."

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["POST"],
    path="/schema/create-category/{month_id}",
    response_model=ResponseDefault,
    endpoint=create_category_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create category for each month.",
)
