from typing import Annotated, Optional
from sqlalchemy.sql import and_
from fastapi import APIRouter, HTTPException, status, Depends, Query
from src.auth.utils.access_token.security import get_current_user
from src.auth.utils.logging import logging
from src.auth.utils.database.general import filter_month_year
from src.auth.schema.response import ResponseDefault
from src.database.connection import database_connection
from src.database.models import money_spend

router = APIRouter(tags=["spends"])

async def list_spending(
    user: Annotated[dict, Depends(get_current_user)],
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=1000, le=9999),
) -> ResponseDefault:
    
    """
        Extract monthly spend information from a specific month:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    """
    
    response = ResponseDefault()
    is_available = await filter_month_year(
        user_uuid=user.user_uuid,
        month=month,
        year=year
    )

    try:
        if not is_available:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schema on {month}/{year} is not created yet.")
        
        logging.info("Endpoint get spend per month.")
        async with database_connection().connect() as session:
            try:
                query = money_spend.select().where(
                    and_(
                        money_spend.c.spend_month == month,
                        money_spend.c.spend_year == year,
                        money_spend.c.user_uuid == user.user_uuid
                    )
                )
                result = await session.execute(query)
                data = result.fetchall()
                logging.info(f"Get spend per month {money_spend.name} on {month}/{year}.")
                response.message = "Get spend per month information success."
                response.data = [dict(row._mapping) for row in data]
                response.success = True
            except Exception as E:
                logging.error(f"Error while getting spend per month inside transaction: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during get spend per month: {E}")
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating spend per month: {E}.")
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
