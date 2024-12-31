from sqlalchemy.sql import and_
from typing import Annotated, Optional
from utils.logger import logging
from services.postgres.models import money_spends
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, Query
from utils.jwt.general import get_current_user
from services.postgres.connection import database_connection
from utils.database.general import filter_month_year, local_time
from utils.custom_error import (
    ServiceError,
    DatabaseError,
    FinanceTrackerApiError,
    EntityDoesNotExistError,
)

router = APIRouter(tags=["Monthly Spend"])


async def list_spending(
    users: Annotated[dict, Depends(get_current_user)],
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=1000, le=9999),
) -> ResponseDefault:
    """
    Extract monthly spend information from a specific month:

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

    if not is_available:
        raise EntityDoesNotExistError(
            detail=f"Schema on {month}/{year} is not created yet.",
        )

    try:
        logging.info("Endpoint get spend per month.")
        async with database_connection().connect() as session:
            try:
                query = money_spends.select().where(
                    and_(
                        money_spends.c.spend_month == month,
                        money_spends.c.spend_year == year,
                        money_spends.c.user_uuid == users.user_uuid,
                    )
                )
                result = await session.execute(query)
                data = result.fetchall()
                logging.info(
                    f"Get spend per month {money_spends.name} on {month}/{year}."
                )
                response.message = "Get spend per month information success."
                response.data = [dict(row._mapping) for row in data]
                response.success = True
            except Exception as E:
                logging.error(f"Error during getting money spend per month: {E}.")
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
    path="/monthly-spend/list",
    response_model=ResponseDefault,
    endpoint=list_spending,
    status_code=status.HTTP_200_OK,
    summary="Get information all spending in specific month based on spesific account.",
)
