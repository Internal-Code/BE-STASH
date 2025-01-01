# from typing import Annotated
# from utils.logger import logging
# from fastapi import APIRouter, status, Depends
# from services.postgres.models import money_spend_schemas
# from src.schema.response import ResponseDefault
# from utils.jwt.general import get_current_user
# from services.postgres.connection import database_connection
# from utils.request_format import MoneySpendSchema
# from utils.database.general import filter_month_year_category, local_time
# from utils.custom_error import (
#     EntityAlreadyExistError,
#     ServiceError,
#     DatabaseError,
#     FinanceTrackerApiError,
# )

# router = APIRouter(tags=["Monthly Schema"])


# async def create_schema(
#     schema: MoneySpendSchema, current_user: Annotated[dict, Depends(get_current_user)]
# ) -> ResponseDefault:
#     """
#     Create a schema with all the information:

#     - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
#     - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
#     - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
#     - **budget**: This specifies the planned amount of money allocated for the category within the specified month and year. The budget represents your spending limit for that particular category during that time frame.
#     """

#     response = ResponseDefault()

#     is_available = await filter_month_year_category(
#         user_uuid=current_user.user_uuid,
#         month=schema.month,
#         year=schema.year,
#         category=schema.category,
#     )

#     if is_available:
#         logging.info(
#             f"User: {current_user.full_name} already have category {schema.category} in {schema.month}/{schema.year}."
#         )
#         raise EntityAlreadyExistError(
#             detail=f"Category {schema.category} already saved.",
#         )

#     try:
#         logging.info("Endpoint create category.")
#         async with database_connection().connect() as session:
#             try:
#                 query = money_spend_schemas.insert().values(
#                     created_at=local_time(),
#                     updated_at=None,
#                     user_uuid=current_user.user_uuid,
#                     month=schema.month,
#                     year=schema.year,
#                     category=schema.category,
#                     budget=schema.budget,
#                 )
#                 await session.execute(query)
#                 await session.commit()
#                 logging.info(f"Created new category: {schema.category}.")
#                 response.message = "Created new category."
#                 response.success = True
#             except Exception as E:
#                 logging.error(f"Error during creating category inside transaction: {E}.")
#                 await session.rollback()
#                 raise DatabaseError(
#                     detail=f"Database error: {E}.",
#                 )
#             finally:
#                 await session.close()
#     except FinanceTrackerApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

#     return response


# router.add_api_route(
#     methods=["POST"],
#     path="/monthly-schema/create",
#     response_model=ResponseDefault,
#     endpoint=create_schema,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a budgeting schema for each month.",
# )
