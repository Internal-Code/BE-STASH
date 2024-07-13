from uuid import UUID
from sqlalchemy.sql import and_
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.access_token.security import get_current_user
from src.auth.routers.dependencies import logging
from src.auth.utils.database.general import filter_month_year
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import GetSchema
from src.database.connection import database_connection
from src.database.models import money_spend_schema

router = APIRouter(tags=["schema"])

async def get_schema(schema: Annotated[GetSchema, Depends()], user:Annotated[dict, Depends(get_current_user)]) -> ResponseDefault:
    
    """
        Extract information from a spesific schema:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    """
    
    response = ResponseDefault()
    is_available = await filter_month_year(
        user_uuid=UUID(user['user_uuid']),
        month=schema.month,
        year=schema.year
    )
    if is_available is False:
        logging.info(f"User {user['username']} is not created schema in {schema.month}/{schema.year}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user['username']} is not created schema in {schema.month}/{schema.year}.")

    try:
        logging.info("Endpoint get category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schema.select().where(
                    and_(
                        money_spend_schema.c.user_uuid == UUID(user['user_uuid']),
                        money_spend_schema.c.month == schema.month,
                        money_spend_schema.c.year == schema.year
                    )
                )
                result = await session.execute(query)
                data = result.fetchall()
                logging.info(f"Get category {money_spend_schema.name} on {schema.month}/{schema.year}.")
                response.message = "Get schema information success."
                response.data = [dict(row._mapping) for row in data]
                response.success = True
            except Exception as E:
                logging.error(f"Error while get category inside transaction: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during get category: {E}")
            finally:
                await session.close()
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    
    return response

router.add_api_route(
    methods=["GET"],
    path="/get_category", 
    response_model=ResponseDefault,
    endpoint=get_schema,
    status_code=status.HTTP_200_OK,
    summary="Get information of spesific schema."
)