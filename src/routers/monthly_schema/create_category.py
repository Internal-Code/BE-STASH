from uuid import UUID
from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import MoneySpendSchema
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from src.schema.request_format import MonthlySchema
from utils.query.general import insert_record, find_record
from utils.custom_error import (
    EntityAlreadyExistError,
    ServiceError,
    DatabaseError,
    StashBaseApiError,
)

router = APIRouter(tags=["Monthly Schema"])


async def create_schema(
    schema: MonthlySchema,
    unique_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    """
    Create a category with all the information:

    - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
    - **budget**: This specifies the planned amount of money allocated for the category within the specified month and year. The budget represents your spending limit for that particular category during that time frame.
    """

    response = ResponseDefault()
    monthly_schema_record = await find_record(db=db, table=MoneySpendSchema, column="unique_id", value=unique_id)

    try:
        if not monthly_schema_record:
            logging.info(f"Category {schema.category} already created.")
            raise EntityAlreadyExistError(detail=f"Category {schema.category} already saved.")

        await insert_record(db=db, table=MoneySpendSchema, data={"category": schema.category, "budget": schema.budget})
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
    path="/monthly-schema/category",
    response_model=ResponseDefault,
    endpoint=create_schema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budgeting schema for each month.",
)
