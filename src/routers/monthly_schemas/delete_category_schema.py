from typing import Annotated
from sqlalchemy.sql import and_
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.models import money_spend_schemas
from src.schema.response import ResponseDefault
from services.postgres.connection import database_connection
from utils.jwt.general import get_current_user
from utils.request_format import DeleteCategorySchema
from utils.database.general import filter_month_year_category
from utils.custom_error import (
    ServiceError,
    DatabaseError,
    FinanceTrackerApiError,
    EntityDoesNotExistError,
)

router = APIRouter(tags=["money-schemas"])


async def update_category_schema(
    schema: DeleteCategorySchema,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    """
    Delete a spesific category of schema:

    - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
    - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent", "Groceries", "Transportation" or any other relevant groupings you define.
    """

    response = ResponseDefault()

    is_available = await filter_month_year_category(
        user_uuid=current_user.user_uuid,
        month=schema.month,
        year=schema.year,
        category=schema.category,
    )

    if is_available is False:
        logging.info(
            f"User {current_user.full_name} does not have the category {schema.category} in {schema.month}/{schema.year}."
        )
        raise EntityDoesNotExistError(
            detail=f"Category {schema.category} not found. Please create category first.",
        )

    try:
        logging.info("Endpoint delete category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schemas.delete().where(
                    and_(
                        money_spend_schemas.c.user_uuid == current_user.user_uuid,
                        money_spend_schemas.c.month == schema.month,
                        money_spend_schemas.c.year == schema.year,
                        money_spend_schemas.c.category == schema.category,
                    )
                )
                await session.execute(query)
                await session.commit()
                logging.info(f"Deleted category {schema.category}.")
                response.message = "Delete category success."
                response.success = True
            except Exception as E:
                logging.error(f"Error during deleting category: {E}.")
                await session.rollback()
                raise DatabaseError(
                    detail=f"Database error: {E}.",
                )
            finally:
                await session.close()
    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["DELETE"],
    path="/delete-category",
    response_model=ResponseDefault,
    endpoint=update_category_schema,
    status_code=status.HTTP_200_OK,
    summary="Delete a budgeting category in spesific month and year.",
)
