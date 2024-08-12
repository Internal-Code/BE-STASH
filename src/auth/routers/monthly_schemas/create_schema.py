from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.utils.jwt.general import get_current_user
from src.auth.utils.database.general import filter_month_year_category, local_time
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import MoneySpendSchema
from src.database.connection import database_connection
from src.database.models import money_spend_schemas

router = APIRouter(tags=["money-schemas"])


async def create_schema(
    schema: MoneySpendSchema, current_user: Annotated[dict, Depends(get_current_user)]
) -> ResponseDefault:
    """
    Create a schema with all the information:

    - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
    - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
    - **budget**: This specifies the planned amount of money allocated for the category within the specified month and year. The budget represents your spending limit for that particular category during that time frame.
    """

    response = ResponseDefault()

    is_available = await filter_month_year_category(
        user_uuid=current_user.user_uuid,
        month=schema.month,
        year=schema.year,
        category=schema.category,
    )

    if is_available:
        logging.info(
            f"User: {current_user.username} already have category {schema.category} in {schema.month}/{schema.year}."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Category {schema.category} already saved.",
        )

    try:
        logging.info("Endpoint create category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schemas.insert().values(
                    created_at=local_time(),
                    updated_at=None,
                    user_uuid=current_user.user_uuid,
                    month=schema.month,
                    year=schema.year,
                    category=schema.category,
                    budget=schema.budget,
                )
                await session.execute(query)
                await session.commit()
                logging.info(f"Created new category: {schema.category}.")
                response.message = "Created new category."
                response.success = True
            except Exception as E:
                logging.error(
                    f"Error during creating category inside transaction: {E}."
                )
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Server error during creating new category: {E}.",
                )
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error after creating category: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["POST"],
    path="/create-schema",
    response_model=ResponseDefault,
    endpoint=create_schema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budgeting schema for each month.",
)
