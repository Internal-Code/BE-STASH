from uuid import UUID
from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import CategorySchema, MonthlySchema
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from src.schema.request_format import MonthlyCategory
from utils.query.general import insert_record, find_record
from utils.custom_error import (
    EntityAlreadyExistError,
    ServiceError,
    DatabaseError,
    StashBaseApiError,
    EntityDoesNotExistError,
)

router = APIRouter(tags=["Monthly Schema"])


async def create_schema(
    schema: MonthlyCategory,
    month_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    """
    Create a category with all the information:

    - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
    - **budget**: This specifies the planned amount of money allocated for the category within the specified month and year. The budget represents your spending limit for that particular category during that time frame.
    """

    response = ResponseDefault()
    category_record = await find_record(
        db=db, table=CategorySchema, unique_id=current_user.unique_id, category=schema.category
    )
    monthly_schema_record = await find_record(db=db, table=MonthlySchema, month_id=str(month_id))

    try:
        if not monthly_schema_record:
            raise EntityDoesNotExistError(detail="Schema not found.")

        if category_record:
            logging.info(f"Category {schema.category} already created.")
            raise EntityAlreadyExistError(detail=f"Category {schema.category} already saved.")

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
    except DatabaseError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["POST"],
    path="/monthly-schema/category/{month_id}",
    response_model=ResponseDefault,
    endpoint=create_schema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budgeting schema for each month.",
)
