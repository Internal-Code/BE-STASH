from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.access_token.security import get_current_active_user
from src.auth.utils.logging import logging
from src.auth.utils.database.general import filter_month_year_category, filter_spesific_category
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import UpdateCategorySchema, local_time
from src.database.connection import database_connection
from src.database.models import money_spend_schema

router = APIRouter(tags=["schema"])

async def update_category_schema(schema: Annotated[UpdateCategorySchema, Depends()], user:Annotated[dict, Depends(get_current_active_user)]) -> ResponseDefault:
    
    """
        Update category information from a spesific month and year:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
        - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
    """
    
    response = ResponseDefault()
    is_available = await filter_month_year_category(
        month=schema.month,
        year=schema.year,
        category=schema.category,
        user_uuid=user.user_uuid
    )
    checked_category = await filter_spesific_category(category=schema.changed_category_into)
    if is_available is False:
        logging.info(f"User {user['username']} is not created schema in {schema.month}/{schema.year}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {schema.category} not found. Please create category first.")
    
    if checked_category is True:
        logging.warning(f"Cannot changed category into: {schema.changed_category_into}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Category {schema.changed_category_into} already saved. Please change with another category.")
    
    try:
        logging.info("Endpoint update category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schema.update().where(
                    money_spend_schema.c.month == schema.month,
                    money_spend_schema.c.year == schema.year,
                    money_spend_schema.c.category == schema.category,
                    money_spend_schema.c.user_uuid == user.user_uuid
                )\
                .values(
                    updated_at = local_time(),
                    category = schema.changed_category_into
                )
                await session.execute(query)
                await session.commit()
                logging.info(f"Updated category {schema.category} into {schema.changed_category_into}.")
                response.message = "Update category success."
                response.success = True
            except Exception as E:
                logging.error(f"Error while updating category: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during updating category: {E}.")
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while updating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["PATCH"],
    path="/update-category", 
    response_model=ResponseDefault,
    endpoint=update_category_schema,
    status_code=status.HTTP_200_OK,
    summary="Update a schema on spesific month and year."
)