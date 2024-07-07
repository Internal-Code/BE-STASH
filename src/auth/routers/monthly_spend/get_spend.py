from src.auth.routers.dependencies import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.database.general import filter_month_year
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import GetSchema
from src.database.connection import database_connection
from src.database.models import money_spend

router = APIRouter(tags=["spend"])

async def get_spend_month(schema: GetSchema = Depends()) -> ResponseDefault:
    
    """
        Extract monthly spend information from a spesific month:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    """
    
    response = ResponseDefault()
    is_available = await filter_month_year(
        month=schema.month,
        year=schema.year
    )

    try:
        if is_available is False:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schema on {schema.month}/{schema.year} is not created yet.")
        else:
            logging.info("Endpoint get spend per month.")
            async with database_connection().connect() as session:
                async with session.begin():
                    try:
                        query = money_spend.select()\
                            .where(money_spend.c.spend_month == schema.month)\
                            .where(money_spend.c.spend_year == schema.year)
                        result = await session.execute(query)
                        data = result.fetchall()
                        logging.info(f"Get spend per month {money_spend.name} on {schema.month}/{schema.year}.")
                        response.message = "Get spend per month information success."
                        response.data = [dict(row._mapping) for row in data]
                        response.success = True
                    except Exception as E:
                        logging.error(f"Error while get spend per month inside transaction: {E}.")
                        await session.rollback()
                        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during get spend per month: {E}")
                    await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating spend per month: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["GET"],
    path="/get_spend_month", 
    response_model=ResponseDefault,
    endpoint=get_spend_month,
    status_code=status.HTTP_200_OK,
    summary="Get information spending in spesific month."
)