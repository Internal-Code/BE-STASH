from typing import Annotated
from uuid import UUID
from sqlalchemy.sql import and_
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.access_token.security import get_current_user
from src.auth.utils.logging import logging
from src.auth.utils.database.general import filter_daily_spending, filter_month_year_category, create_category_format
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import UpdateCategorySpending, local_time
from src.database.connection import database_connection
from src.database.models import money_spend, money_spend_schema

router = APIRouter(tags=["spend"])

async def update_monthly_spend(schema: Annotated[UpdateCategorySpending, Depends()], user:Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    
    """
        Update category information for a specific month and year.

        The endpoint allows you to update the details of an existing spending record, such as the date, category, description, and amount.

        - **spend_day**: The day of the original spending record.
        - **changed_spend_day**: The new day for the spending record.
        - **spend_month**: The month of the original spending record.
        - **changed_spend_month**: The new month for the spending record.
        - **spend_year**: The year of the original spending record.
        - **changed_spend_year**: The new year for the spending record.
        - **category**: The original category of the spending record.
        - **changed_category_into**: The new category for the spending record.
        - **description**: The original description of the spending record.
        - **changed_description_into**: The new description for the spending record.
        - **amount**: The original amount of the spending record.
        - **changed_amount_into**: The new amount for the spending record.
    """
    
    response = ResponseDefault()
    
    try:
        spending_is_available = await filter_daily_spending(
            user_uuid=user.user_uuid,
            amount=schema.amount,
            description=schema.description,
            category=schema.category,
            spend_day=schema.spend_day,
            spend_month=schema.spend_month,
            spend_year=schema.spend_year
        )
        
        category_is_available = await filter_month_year_category(
            user_uuid=user.user_uuid,
            month=schema.changed_spend_month,
            year=schema.changed_spend_year,
            category=schema.changed_category_into
        )
        print(category_is_available)
    
        if spending_is_available is False:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data daily spending {schema.spend_day}/{schema.spend_month}/{schema.spend_year} {schema.category}/{schema.description}/{schema.amount} not found. Please create first.")
        else:
            logging.info("Endpoint update daily spend data.")
            async with database_connection().connect() as session:
                try:
                    if category_is_available is False:
                        create_category = create_category_format(
                            user_uuid=user.user_uuid,
                            category=schema.changed_category_into,
                            month=schema.changed_spend_month,
                            year=schema.changed_spend_year,
                        )
                        created_category = money_spend_schema.insert().values(create_category)
                        updated_daily_spend = money_spend.update().where(
                            and_(
                                money_spend.c.spend_day == schema.spend_day,
                                money_spend.c.spend_month == schema.spend_month,
                                money_spend.c.spend_year == schema.spend_year,
                                money_spend.c.category == schema.category,
                                money_spend.c.description == schema.description,
                                money_spend.c.amount == schema.amount,
                            )
                        ).values(
                            updated_at = local_time(),
                            spend_day = schema.changed_spend_day,
                            spend_month = schema.changed_spend_month,
                            spend_year = schema.changed_spend_year,
                            category = schema.changed_category_into,
                            description = schema.changed_description_into,
                            amount = schema.changed_amount_into
                        )
                        await session.execute(created_category)
                        await session.execute(updated_daily_spend)
                        await session.commit()
                        logging.info("Updated spend money and created schema.")
                        response.message = "Created new schema category and updated daily spending data."
                        response.success = True
                    else:
                        updated_daily_spend = money_spend.update().where(
                            money_spend.c.spend_day == schema.spend_day,
                            money_spend.c.spend_month == schema.spend_month,
                            money_spend.c.spend_year == schema.spend_year,
                            money_spend.c.category == schema.category,
                            money_spend.c.description == schema.description,
                            money_spend.c.amount == schema.amount
                        ).values(
                            updated_at = local_time(),
                            spend_day = schema.changed_spend_day,
                            spend_month = schema.changed_spend_month,
                            spend_year = schema.changed_spend_year,
                            category = schema.changed_category_into,
                            description = schema.changed_description_into,
                            amount = schema.changed_amount_into
                        )
                        await session.execute(updated_daily_spend)
                        await session.commit()
                        logging.info(f"Updated category {schema.category} into {schema.changed_category_into}.")
                        response.message = "Update daily spending data success."
                        response.success = True
                except Exception as E:
                    logging.error(f"Error while daily spending data: {E}.")
                    await session.rollback()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during daily spending creation: {E}.")
                finally:
                    await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while updating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["PUT"],
    path="/update-monthly-spend", 
    response_model=ResponseDefault,
    endpoint=update_monthly_spend,
    status_code=status.HTTP_200_OK,
    summary="Update a schema on spesific month and year."
)