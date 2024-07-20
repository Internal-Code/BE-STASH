from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.access_token.security import get_current_user
from src.auth.utils.logging import logging
from src.auth.utils.database.general import create_spending_format, filter_month_year_category, create_category_format
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import CreateSpend
from src.database.connection import database_connection
from src.database.models import money_spends, money_spend_schemas

router = APIRouter(tags=["spends"])

async def create_spend(schema: CreateSpend, users:Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    
    """
        Create a money spend data with all the information:

        - **spend_day**: This refers to the specific calendar date (e.g., 1, 2 ... 31) when the schema was created or applies to.
        - **spend_month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **spend_year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
        - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
        - **description**: A description or note about the spending.
        - **amount**: The amount of money spent.
    """
    
    response = ResponseDefault()
    try:
            
        is_available = await filter_month_year_category(
            user_uuid=users.user_uuid,
            month=schema.spend_month,
            year=schema.spend_year,
            category=schema.category
        )
        
        prepared_spend = create_spending_format(
            user_uuid=users.user_uuid,
            category=schema.category,
            description=schema.description,
            amount=schema.amount,
            spend_day=schema.spend_day,
            spend_month=schema.spend_month,
            spend_year=schema.spend_year
        )
        
        logging.info("Endpoint create spend money.")
        async with database_connection().connect() as session:
            async with session.begin():
                try:
                    if not is_available:
                        logging.info(f"Inserting data into table {money_spends.name} and {money_spend_schemas.name}")
                        
                        prepared_category = create_category_format(
                            user_uuid=users.user_uuid,
                            month=schema.spend_month,
                            year=schema.spend_year,
                            category=schema.category
                        )
                        
                        create_spend = money_spends.insert().values(prepared_spend)
                        create_category = money_spend_schemas.insert().values(prepared_category)
                        await session.execute(create_spend)
                        await session.execute(create_category)
                        logging.info("Created new spend money and schema.")
                        response.message = "Created new spend money and schema data."
                        response.success = True
                    else:
                        logging.info(f"Only inserting data into table {money_spends.name}")
                        create_spend = money_spends.insert().values(prepared_spend)
                        await session.execute(create_spend)
                        logging.info("Created new spend money.")
                        response.message = "Created new spend money."
                        response.success = True
                except Exception as E:
                    logging.error(f"Error while creating spend money inside transaction: {E}.")
                    await session.rollback()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during transaction: {E}.")
                finally:
                    await session.commit()
            await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating spend money: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response
        
router.add_api_route(
    methods=["POST"],
    path="/create-spend", 
    response_model=ResponseDefault,
    endpoint=create_spend,
    status_code=status.HTTP_201_CREATED,
    summary="Create daily spend record."
)