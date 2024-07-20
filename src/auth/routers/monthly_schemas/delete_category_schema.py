from typing import Annotated
from sqlalchemy.sql import and_
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.logging import logging
from src.auth.utils.access_token.security import get_current_user
from src.auth.utils.database.general import filter_month_year_category
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import DeleteCategorySchema
from src.database.connection import database_connection
from src.database.models import money_spend_schemas

router = APIRouter(tags=["schemas"])

async def update_category_schema(schema: DeleteCategorySchema, users:Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    
    """
        Delete a spesific category of schema:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
        - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent", "Groceries", "Transportation" or any other relevant groupings you define.
    """
    
    response = ResponseDefault()
    try:
        isAvailable = await filter_month_year_category(
            user_uuid=users.user_uuid,
            month=schema.month,
            year=schema.year,
            category=schema.category
        )

        if isAvailable is False:
            logging.info(f"User {users.username} does not have the category {schema.category} in {schema.month}/{schema.year}.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {schema.category} not found. Please create category first.")
        
        logging.info("Endpoint delete category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schemas.delete().where(
                    and_(
                        money_spend_schemas.c.user_uuid == users.user_uuid,
                        money_spend_schemas.c.month == schema.month,
                        money_spend_schemas.c.year == schema.year,
                        money_spend_schemas.c.category == schema.category
                    )
                )
                await session.execute(query)
                await session.commit()
                logging.info(f"Deleted category {schema.category}.")
                response.message="Delete category success."
                response.success=True
            except Exception as E:
                logging.error(f"Error during deleting category: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Server error during deleting category: {E}.")
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error after updating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["DELETE"],
    path="/delete-category", 
    response_model=ResponseDefault,
    endpoint=update_category_schema,
    status_code=status.HTTP_200_OK,
    summary="Delete a budgeting category in spesific month and year."
)