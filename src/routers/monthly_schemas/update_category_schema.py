from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends
from services.postgres.models import money_spend_schemas
from src.schema.response import ResponseDefault
from utils.jwt.general import get_current_user
from services.postgres.connection import database_connection
from utils.request_format import UpdateCategorySchema, local_time
from utils.database.general import (
    filter_month_year_category,
    filter_spesific_category,
)
from utils.custom_error import (
    EntityAlreadyExistError,
    ServiceError,
    DatabaseError,
    FinanceTrackerApiError,
    EntityDoesNotExistError,
)

router = APIRouter(tags=["money-schemas"])


async def update_category_schema(
    schema: UpdateCategorySchema,
    current_users: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    """
    Update category information from a spesific month and year:

    - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
    - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
    """

    response = ResponseDefault()

    is_available = await filter_month_year_category(
        month=schema.month,
        year=schema.year,
        category=schema.category,
        user_uuid=current_users.user_uuid,
    )

    category_already_saved = await filter_spesific_category(
        category=schema.changed_category_into, user_uuid=current_users.user_uuid
    )

    if is_available is False:
        logging.info(
            f"User {current_users.full_name} is not created schema in {schema.month}/{schema.year}."
        )
        raise EntityDoesNotExistError(
            detail=f"Category {schema.category} not found. Please create category first."
        )

    if category_already_saved is True:
        logging.warning(
            f"Cannot changed category into: {schema.changed_category_into}."
        )
        raise EntityAlreadyExistError(
            detail=f"Category {schema.changed_category_into} already saved. Please change with another category."
        )

    try:
        logging.info("Endpoint update category.")
        async with database_connection().connect() as session:
            try:
                query = (
                    money_spend_schemas.update()
                    .where(
                        money_spend_schemas.c.month == schema.month,
                        money_spend_schemas.c.year == schema.year,
                        money_spend_schemas.c.category == schema.category,
                        money_spend_schemas.c.user_uuid == current_users.user_uuid,
                    )
                    .values(
                        updated_at=local_time(), category=schema.changed_category_into
                    )
                )
                await session.execute(query)
                await session.commit()
                logging.info(
                    f"Updated category {schema.category} into {schema.changed_category_into}."
                )
                response.message = "Update category success."
                response.success = True
            except Exception as E:
                logging.error(f"Error during updating category: {E}.")
                await session.rollback()
                raise DatabaseError(detail=f"Database error: {E}.")
            finally:
                await session.close()
    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/update-category",
    response_model=ResponseDefault,
    endpoint=update_category_schema,
    status_code=status.HTTP_200_OK,
    summary="Update a schema on spesific month and year.",
)
