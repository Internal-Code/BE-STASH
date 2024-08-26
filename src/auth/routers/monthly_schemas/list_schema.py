from sqlalchemy.sql import and_
from typing import Annotated, Optional
from src.auth.utils.logging import logging
from src.database.models import money_spend_schemas
from src.auth.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, Query
from src.auth.utils.jwt.general import get_current_user
from src.database.connection import database_connection
from src.auth.utils.database.general import filter_month_year, local_time
from src.auth.routers.exceptions import (
    ServiceError,
    DatabaseError,
    FinanceTrackerApiError,
    EntityDoesNotExistError,
)

router = APIRouter(tags=["money-schemas"])


async def list_schema(
    users: Annotated[dict, Depends(get_current_user)],
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=1000, le=9999),
) -> ResponseDefault:
    """
    Extract information from a specific schema:

    - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
    - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    """

    current_time = local_time()
    month = month if month is not None else current_time.month
    year = year if year is not None else current_time.year

    response = ResponseDefault()

    is_available = await filter_month_year(
        user_uuid=users.user_uuid, month=month, year=year
    )

    if is_available is False:
        logging.info(
            f"User {users.username} has not created a schema in {month}/{year}."
        )
        raise EntityDoesNotExistError(
            detail=f"User {users.username} has not created a schema in {month}/{year}."
        )

    try:
        logging.info("Endpoint get category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schemas.select().where(
                    and_(
                        money_spend_schemas.c.user_uuid == users.user_uuid,
                        money_spend_schemas.c.month == month,
                        money_spend_schemas.c.year == year,
                    )
                )
                result = await session.execute(query)
                data = result.fetchall()
                logging.info(
                    f"Get category {money_spend_schemas.name} for {month}/{year}."
                )
                response.message = "Get schema information success."
                response.data = [dict(row._mapping) for row in data]
                response.success = True
            except Exception as E:
                logging.error(f"Error during get category: {E}.")
                await session.rollback()
                raise DatabaseError(
                    detail=f"Database error: {E}",
                )
            finally:
                await session.close()
    except FinanceTrackerApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["GET"],
    path="/list-category",
    response_model=ResponseDefault,
    endpoint=list_schema,
    status_code=status.HTTP_200_OK,
    summary="Get all schema information for a specific account.",
)
