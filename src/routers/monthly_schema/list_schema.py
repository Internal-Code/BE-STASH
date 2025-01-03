from fastapi import APIRouter, status, Depends, Query
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from services.postgres.models import MonthlySchema
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.query.general import find_record

# from utils.database.general import filter_month_year, local_time
from utils.helper import local_time
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
)

router = APIRouter(tags=["Monthly Schema"])


async def list_schema(
    current_user: Annotated[dict, Depends(get_current_user)],
    month: Optional[int] = Query(default=local_time().month, ge=1, le=12),
    year: Optional[int] = Query(default=local_time().year, ge=1000, le=9999),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    """
    Extract information from a specific schema:

    - **month**: This refers to the specific calendar month (e.g., January, February) when the schema was created or applies to.
    - **year**: This represents the calendar year (e.g., 2023, 2024) associated with the schema.
    """

    response = ResponseDefault()

    # is_available = await filter_month_year(user_uuid=users.user_uuid, month=month, year=year)

    # if is_available is False:
    #     logging.info(f"User {users.full_name} has not created a schema in {month}/{year}.")
    #     raise EntityDoesNotExistError(
    #         detail=f"User {users.full_name} has not created a schema in {month}/{year}."
    #     )

    try:
        entries = await find_record(db=db, table=MonthlySchema, fetch_type="all", unique_id=current_user.unique_id)
        if entries:
            response.message = f"Extracted {len(entries)}."
            response.data = entries
        pass
        # logging.info("Endpoint get category.")
        # async with database_connection().connect() as session:
        #     try:
        #         query = money_spend_schemas.select().where(
        #             and_(
        #                 money_spend_schemas.c.user_uuid == users.user_uuid,
        #                 money_spend_schemas.c.month == month,
        #                 money_spend_schemas.c.year == year,
        #             )
        #         )
        #         result = await session.execute(query)
        #         data = result.fetchall()
        #         logging.info(f"Get category {money_spend_schemas.name} for {month}/{year}.")
        #         response.message = "Get schema information success."
        #         response.data = [dict(row._mapping) for row in data]
        #         response.success = True
        #     except Exception as E:
        #         logging.error(f"Error during get category: {E}.")
        #         await session.rollback()
        #         raise DatabaseError(
        #             detail=f"Database error: {E}",
        #         )
        #     finally:
        #         await session.close()

    except StashBaseApiError as FTE:
        raise FTE

    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["GET"],
    path="/monthly-schema/list",
    response_model=ResponseDefault,
    endpoint=list_schema,
    status_code=status.HTTP_200_OK,
    summary="Get all schema information for a specific account.",
)
