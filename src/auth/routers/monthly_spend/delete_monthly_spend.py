from src.auth.routers.dependencies import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.database.general import create_spending_format, filter_daily_spending
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import CreateSpend
from src.database.connection import database_connection
from src.database.models import money_spend, money_spend_schema

router = APIRouter(tags=["spend"])

async def create_spend(schema: CreateSpend = Depends()) -> ResponseDefault:
    
    """
        Delete spesific money spend data with all the information:

        - **spend_day**: This refers to the specific calendar date (e.g., 1, 2 ... 31) when the schema was created or applies to.
        - **spend_month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **spend_year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
        - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
        - **description**: A description or note about the spending.
        - **amount**: The amount of money spent.
    """
    
    response = ResponseDefault()
    try:
            
        is_available = await filter_daily_spending(
            amount=schema.amount,
            description=schema.description,
            category=schema.category,
            spend_day=schema.spend_day,
            spend_month=schema.spend_month,
            spend_year=schema.spend_year
        )
        
        if not is_available:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data is not found. Ensure selected data already created on database.")
        
        logging.info("Endpoint create spend money.")
        async with database_connection().connect() as session:
            async with session.begin():
                try:
                    logging.info(f"Deleting daily spending record.")
                    create_spend = money_spend.delete()\
                        .where(money_spend.c.spend_day == schema.spend_day)\
                        .where(money_spend.c.spend_month == schema.spend_month)\
                        .where(money_spend.c.spend_year == schema.spend_year)\
                        .where(money_spend.c.category == schema.category)\
                        .where(money_spend.c.description == schema.description)\
                        .where(money_spend.c.amount == schema.amount)
                    await session.execute(create_spend)
                    logging.info("Deleted a daily spend record.")
                    response.message = "Delete daily spend data success."
                    response.success = True
                except Exception as E:
                    logging.error(f"Error during delete daily spend money data: {E}.")
                    await session.rollback()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during transaction: {E}.")
                finally:
                    await session.commit()
            await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error after deleting daily spend money data: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response
        
router.add_api_route(
    methods=["DELETE"],
    path="/delete_spend", 
    response_model=ResponseDefault,
    endpoint=create_spend,
    status_code=status.HTTP_201_CREATED,
    summary="Delete daily spend record."
)