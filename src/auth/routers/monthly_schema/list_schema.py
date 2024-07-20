from sqlalchemy.sql import and_
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from src.auth.utils.access_token.security import get_current_user
from src.auth.utils.logging import logging
from src.auth.utils.database.general import filter_month_year, local_time
from src.auth.schema.response import ResponseDefault
from src.database.connection import database_connection
from src.database.models import money_spend_schema

router = APIRouter(tags=["schemas"])

async def list_schema(
    user: Annotated[dict, Depends(get_current_user)],
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
        user_uuid=user.user_uuid,
        month=month,
        year=year
    )
    if is_available is False:
        logging.info(f"User {user.username} has not created a schema in {month}/{year}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user.username} has not created a schema in {month}/{year}.")

    try:
        logging.info("Endpoint get category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schema.select().where(
                    and_(
                        money_spend_schema.c.user_uuid == user.user_uuid,
                        money_spend_schema.c.month == month,
                        money_spend_schema.c.year == year
                    )
                )
                result = await session.execute(query)
                data = result.fetchall()
                logging.info(f"Get category {money_spend_schema.name} for {month}/{year}.")
                response.message = "Get schema information success."
                response.data = [dict(row._mapping) for row in data]
                response.success = True
            except Exception as E:
                logging.error(f"Error while getting category inside transaction: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during get category: {E}")
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while getting category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["GET"],
    path="/list-category", 
    response_model=ResponseDefault,
    endpoint=list_schema,
    status_code=status.HTTP_200_OK,
    summary="Get all schema information for a specific account."
)