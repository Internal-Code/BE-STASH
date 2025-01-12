# from typing import Annotated
# from sqlalchemy.sql import update, and_
# from utils.logger import logging
# from services.postgres.models import money_spends
# from fastapi import APIRouter, status, Depends
# from src.schema.response import ResponseDefault
# from utils.jwt.general import get_current_user
# from services.postgres.connection import database_connection
# from utils.request_format import UpdateCategorySpending, local_time
# from utils.custom_error import (
#     ServiceError,
#     DatabaseQueryError,
#     StashBaseApiError,
#     DataNotFoundError,
# )
# from utils.database.general import (
#     filter_daily_spending,
#     filter_spesific_category,
# )

# router = APIRouter(tags=["Monthly Spend"])


# async def update_monthly_spend(
#     schema: UpdateCategorySpending,
#     current_user: Annotated[dict, Depends(get_current_user)],
# ) -> ResponseDefault:
#     """
#     Update category information for a specific month and year.

#     The endpoint allows you to update the details of an existing spending record, such as the date, category, description, and amount.

#     - **spend_day**: The day of the original spending record.
#     - **changed_spend_day**: The new day for the spending record.
#     - **spend_month**: The month of the original spending record.
#     - **changed_spend_month**: The new month for the spending record.
#     - **spend_year**: The year of the original spending record.
#     - **changed_spend_year**: The new year for the spending record.
#     - **category**: The original category of the spending record.
#     - **changed_category_into**: The new category for the spending record.
#     - **description**: The original description of the spending record.
#     - **changed_description_into**: The new description for the spending record.
#     - **amount**: The original amount of the spending record.
#     - **changed_amount_into**: The new amount for the spending record.
#     """

#     response = ResponseDefault()

#     category_already_saved = await filter_spesific_category(
#         category=schema.changed_category_into, user_uuid=current_user.user_uuid
#     )

#     if not category_already_saved:
#         raise DataNotFoundError(
#             detail=f"Category {schema.changed_category_into} is not found on database. You should create it first."
#         )

#     spending_is_available = await filter_daily_spending(
#         user_uuid=current_user.user_uuid,
#         amount=schema.amount,
#         description=schema.description,
#         category=schema.category,
#         spend_day=schema.spend_day,
#         spend_month=schema.spend_month,
#         spend_year=schema.spend_year,
#     )

#     if not spending_is_available:
#         raise DataNotFoundError(
#             detail=f"Data daily spending on {schema.spend_day}/{schema.spend_month}/{schema.spend_year} with category {schema.category} not found. Please create first."
#         )

#     try:
#         logging.info("Endpoint update daily spend data.")
#         async with database_connection().connect() as session:
#             try:
#                 updated_daily_spend = (
#                     update(money_spends)
#                     .where(
#                         and_(
#                             money_spends.c.id == spending_is_available.id,
#                             money_spends.c.user_uuid == spending_is_available.user_uuid,
#                         )
#                     )
#                     .values(
#                         updated_at=local_time(),
#                         spend_day=schema.changed_spend_day,
#                         spend_month=schema.changed_spend_month,
#                         spend_year=schema.changed_spend_year,
#                         category=schema.changed_category_into,
#                         description=schema.changed_description_into,
#                         amount=schema.changed_amount_into,
#                     )
#                 )
#                 await session.execute(updated_daily_spend)
#                 await session.commit()
#                 logging.info(
#                     f"Updated category {schema.category} into {schema.changed_category_into}."
#                 )
#                 response.message = "Update daily spending data success."
#                 response.success = True
#             except Exception as E:
#                 logging.error(f"Error while daily spending data: {E}.")
#                 await session.rollback()
#                 raise DatabaseQueryError(
#                     detail=f"Database error: {E}.",
#                 )
#             finally:
#                 await session.close()
#     except StashBaseApiError as FTE:
#         raise FTE

#     except Exception as E:
#         raise ServiceError(detail=f"Service error: {E}.", name="STASH")

#     return response


# router.add_api_route(
#     methods=["PATCH"],
#     path="/monthly-spend/update",
#     response_model=ResponseDefault,
#     endpoint=update_monthly_spend,
#     status_code=status.HTTP_200_OK,
#     summary="Update a schema on spesific month and year.",
# )
