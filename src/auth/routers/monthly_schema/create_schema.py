from src.auth.routers.dependencies import logging
from src.auth.utils.access_token.jwt import get_current_user, oauth2_scheme
from fastapi import APIRouter, HTTPException, status, Depends
from src.auth.utils.database.general import create_category_format, filter_month_year_category
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import MoneySpendSchema
from src.database.connection import database_connection
from src.database.models import money_spend_schema

router = APIRouter(tags=["schema"])

async def create_schema(schema: MoneySpendSchema, token: str = Depends(oauth2_scheme)) -> ResponseDefault:
    """
        Create a schema with all the information:

        - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
        - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
        - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
        - **budget**: This specifies the planned amount of money allocated for the category within the specified month and year. The budget represents your spending limit for that particular category during that time frame.
    """

    response = ResponseDefault()
    user = get_current_user(token)
    print(user)
    try:
        isAvailable = await filter_month_year_category(
            month=schema.month,
            year=schema.year,
            category=schema.category
        )
        if isAvailable:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Category {schema.category} already saved.")

        preparedData = create_category_format(
            month=schema.month, 
            year=schema.year, 
            category=schema.category, 
            budget=schema.budget
        )

        logging.info("Endpoint create category.")
        async with database_connection().connect() as session:
            try:
                query = money_spend_schema.insert().values(preparedData)
                await session.execute(query)
                await session.commit()
                logging.info(f"Created new category: {schema.category}.")
            except Exception as E:
                logging.error(f"Error while creating category inside transaction: {E}.")
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error during transaction: {E}.")
            finally:
                await session.close()

        response.message = "Created new category."
        response.success = True
    except HTTPException as E:
        raise E
    except Exception as E:
        logging.error(f"Error while creating category: {E}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {E}.")
    return response

router.add_api_route(
    methods=["POST"],
    path="/create_schema", 
    response_model=ResponseDefault,
    endpoint=create_schema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a budgeting schema for each month.",
    dependencies=[Depends(get_current_user)]
)