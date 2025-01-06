# from typing import Annotated
# from utils.logger import logging
# from services.postgres.models import money_spends
# from fastapi import APIRouter, status, Depends
# from src.schema.response import ResponseDefault
# from utils.jwt.general import get_current_user
# from utils.request_format import CreateSpend
# from services.postgres.connection import database_connection
# from utils.database.general import filter_daily_spending
# from utils.custom_error import (
#     ServiceError,
#     DatabaseQueryError,
#     StashBaseApiError,
#     DataNotFoundError,
# )

# router = APIRouter(tags=["Monthly Spend"])


# async def create_spend(
#     schema: CreateSpend, users: Annotated[dict, Depends(get_current_user)]
# ) -> ResponseDefault:
#     """
#     Delete spesific money spend data with all the information:

#     - **spend_day**: This refers to the specific calendar date (e.g., 1, 2 ... 31) when the schema was created or applies to.
#     - **spend_month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
#     - **spend_year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
#     - **category**: This identifies the type of expense or area the schema pertains to. Examples of categories could be "Rent," "Groceries," "Transportation," or any other relevant groupings you define.
#     - **description**: A description or note about the spending.
#     - **amount**: The amount of money spent.
#     """

#     response = ResponseDefault()

#     is_available = await filter_daily_spending(
#         user_uuid=users.user_uuid,
#         amount=schema.amount,
#         description=schema.description,
#         category=schema.category,
#         spend_day=schema.spend_day,
#         spend_month=schema.spend_month,
#         spend_year=schema.spend_year,
#     )

#     if not is_available:
#         raise DataNotFoundError(
#             detail="Data is not found. Please ensure data already created on database."
#         )

#     try:
#         logging.info("Endpoint create spend money.")
#         async with database_connection().connect() as session:
#             try:
#                 logging.info("Deleting daily spending record.")
#                 create_spend = money_spends.delete().where(
#                     money_spends.c.id == is_available.id,
#                     money_spends.c.spend_day == is_available.spend_day,
#                     money_spends.c.spend_month == is_available.spend_month,
#                     money_spends.c.spend_year == is_available.spend_year,
#                     money_spends.c.category == is_available.category,
#                     money_spends.c.description == is_available.description,
#                     money_spends.c.amount == is_available.amount,
#                     money_spends.c.user_uuid == users.user_uuid,
#                 )
#                 await session.execute(create_spend)
#                 await session.commit()
#                 logging.info("Deleted a daily spend record.")
#                 response.message = "Delete daily spend data success."
#                 response.success = True
#             except Exception as E:
#                 logging.error(f"Error during delete daily spend money data: {E}.")
#                 await session.rollback()
#                 raise DatabaseQueryError(
#                     detail=f"Database error: {E}.",
#                 )
#             finally:
#                 await session.close()
#     except StashBaseApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

#     return response


# router.add_api_route(
#     methods=["PATCH"],
#     path="/monthly-spend/delete",
#     response_model=ResponseDefault,
#     endpoint=create_spend,
#     status_code=status.HTTP_201_CREATED,
#     summary="Delete daily spend record.",
# )
