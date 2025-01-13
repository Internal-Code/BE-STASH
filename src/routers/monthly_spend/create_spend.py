# from typing import Annotated
# from utils.logger import logging
# from fastapi import APIRouter, status, Depends
# from src.schema.response import ResponseDefault
# from utils.request_format import CreateSpend
# from utils.jwt.general import get_current_user
# from services.postgres.connection import database_connection
# from services.postgres.models import money_spends, money_spend_schemas
# from utils.database.general import filter_month_year_category, local_time
# from utils.custom_error import (
#     ServiceError,
#     DatabaseQueryError,
#     StashBaseApiError,
# )

# router = APIRouter(tags=["Monthly Spend"])


# async def create_spend(
#     schema: CreateSpend, current_user: Annotated[dict, Depends(get_current_user)]
# ) -> ResponseDefault:
#     """
#     Create a money spend data with all the information:

#     - **spend_day**: This refers to the specific calendar date (e.g., 1, 2 ... 31) when the schema was created or applies to.
#     - **spend_month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
#     - **spend_year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
#     - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
#     - **description**: A description or note about the spending.
#     - **amount**: The amount of money spent.
#     """

#     response = ResponseDefault()

#     is_available = await filter_month_year_category(
#         user_uuid=current_user.user_uuid,
#         month=schema.spend_month,
#         year=schema.spend_year,
#         category=schema.category,
#     )

#     try:
#         logging.info("Endpoint create spend money.")
#         async with database_connection().connect() as session:
#             try:
#                 if is_available is False:
#                     try:
#                         logging.info(
#                             f"Inserting data into table {money_spends.name} and {money_spend_schemas.name}"
#                         )

#                         create_spend = money_spends.insert().values(
#                             created_at=local_time(),
#                             updated_at=None,
#                             user_uuid=current_user.user_uuid,
#                             spend_day=schema.spend_day,
#                             spend_month=schema.spend_month,
#                             spend_year=schema.spend_year,
#                             category=schema.category,
#                             description=schema.description,
#                             amount=schema.amount,
#                         )
#                         create_category = money_spend_schemas.insert().values(
#                             created_at=local_time(),
#                             updated_at=None,
#                             user_uuid=current_user.user_uuid,
#                             month=schema.spend_month,
#                             year=schema.spend_year,
#                             category=schema.category,
#                             budget=0,
#                         )
#                         await session.execute(create_spend)
#                         await session.execute(create_category)
#                         await session.commit()
#                         logging.info("Created new spend money and schema.")
#                         response.message = "Created new spend money and schema data."
#                         response.success = True
#                     except Exception as E:
#                         logging.error(f"Error during creating new spend money and schema: {E}.")
#                         await session.rollback()
#                         raise DatabaseQueryError(detail=f"Database error: {E}.")
#                 else:
#                     try:
#                         logging.info(f"Only inserting data into table {money_spends.name}")
#                         create_spend = money_spends.insert().values(
#                             created_at=local_time(),
#                             updated_at=None,
#                             user_uuid=current_user.user_uuid,
#                             spend_day=schema.spend_day,
#                             spend_month=schema.spend_month,
#                             spend_year=schema.spend_year,
#                             category=schema.category,
#                             description=schema.description,
#                             amount=schema.amount,
#                         )
#                         await session.execute(create_spend)
#                         await session.commit()
#                         logging.info("Created new spend money.")
#                         response.message = "Created new spend money."
#                         response.success = True
#                     except Exception as E:
#                         logging.error(f"Error during creating new spend money: {E}.")
#                         await session.rollback()
#                         raise DatabaseQueryError(detail=f"Database error: {E}.")
#             except Exception as E:
#                 logging.error(
#                     f"Error during creating spend money or with adding money schema: {E}."
#                 )
#                 await session.rollback()
#                 raise DatabaseQueryError(
#                     detail=f"Database error during creating spend money or with adding money schema: {E}."
#                 )
#             finally:
#                 await session.close()
#     except StashBaseApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="STASH")

#     return response


# router.add_api_route(
#     methods=["POST"],
#     path="/monthly-spend/create",
#     response_model=ResponseDefault,
#     endpoint=create_spend,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create daily spend record.",
# )
