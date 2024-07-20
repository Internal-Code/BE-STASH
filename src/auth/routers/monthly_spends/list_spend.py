from typing import Annotated, Optional
from sqlalchemy.sql import and_
from fastapi import APIRouter, HTTPException, status, Depends, Query
from src.auth.utils.access_token.security import get_current_user
from src.auth.utils.logging import logging
from src.auth.utils.database.general import filter_month_year, local_time
from src.auth.schema.response import ResponseDefault
from src.database.connection import database_connection
from src.database.models import money_spends

router = APIRouter(tags=["money-spends"])

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
        user_uuid=users.user_uuid,
        month=month,
        year=year
    )
    
    if not is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schema on {month}/{year} is not created yet.")

    try:
        logging.info("Endpoint get spend per month.")
        async with database_connection().connect() as session:
            try:
                query = money_spends.select().where(
                    and_(
                        money_spends.c.spend_month == month,
                        money_spends.c.spend_year == year,
                        money_spends.c.user_uuid == users.user_uuid
                    )
                )
                result = await session.execute(query)
                data = result.fetchall()
                logging.info(f"Get spend per month {money_spends.name} on {month}/{year}.")
                response.message = "Get spend per month information success."
                response.data = [dict(row._mapping) for row in data]
                response.success = True
            except Exception as E:
                logging.error(f"Error during getting money spend per month: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Server error during getting money spend per month: {E}")
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error after getting money spend per month: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["GET"],
    path="/list-spending", 
    response_model=ResponseDefault,
    endpoint=list_spending,
    status_code=status.HTTP_200_OK,
    summary="Get information all spending in specific month based on spesific account."
)
