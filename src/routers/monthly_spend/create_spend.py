from uuid import uuid4
from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.helper import leap_year
from utils.query import QueryDatabase
from src.schema.response import ResponseDefault
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, status, Depends, Path
from src.schema.request_format import CreateSpendPayload
from services.postgres.models import MonthlySchema, CategorySchema, MoneySpend
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    EntityDoesNotMatchedError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Spend"], prefix="/spend")


async def create_spend_endpoint(
    schema: CreateSpendPayload,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    day: int = Path(ge=1, le=31, description="Day should be between 1 and 31"),
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year should be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Create spend endpoint.")
    response = ResponseDefault()
    spend_id = str(uuid4())
    year = int(year)
    query = QueryDatabase(db)

    try:
        monthly_schema_record = await query.find(
            table=MonthlySchema,
            unique_id=current_user.unique_id,
            month=month,
            year=year,
            deleted_at=None,
        )

        if not monthly_schema_record:
            logging.error(f"Schema {month}/{year} not found.")
            raise DataNotFoundError(detail="Schema not found.")

        month_id = monthly_schema_record.month_id

        category_record = await query.find(
            table=CategorySchema,
            unique_id=current_user.unique_id,
            month_id=month_id,
            category=schema.category,
        )

        if not category_record:
            logging.error(f"Category {schema.category} not found.")
            raise DataNotFoundError(detail="Category not found.")

        category_id = category_record.category_id

        is_leap_year = leap_year(year=year)
        fixed_day = [4, 6, 9, 11]

        if month == 2:
            logging.warning("Validating process on month February.")
            if is_leap_year and day > 29:
                logging.error(f"Invalid day {day} in February of a leap year.")
                raise EntityDoesNotMatchedError(
                    detail="Day should be 29 or less in February of a leap year."
                )
            if not is_leap_year and day > 28:
                logging.error(f"Invalid day {day} in February of a non-leap year.")
                raise EntityDoesNotMatchedError(
                    detail="Day should be 28 or less in February of a non-leap year."
                )

        if month in fixed_day and day > 30:
            logging.error(f"Invalid day {day} for month {month}.")
            raise EntityDoesNotMatchedError(
                detail="Day should be 30 or less for this month."
            )

        await query.insert(
            table=MoneySpend,
            data={
                "unique_id": current_user.unique_id,
                "spend_id": spend_id,
                "category_id": category_id,
                "month_id": month_id,
                "day": day,
                "category": schema.category,
                "amount": schema.amount,
                "description": schema.description,
            },
        )
        response.message = "Daily spend sucessfully created."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/create/{day}/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=create_spend_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create daily money spend.",
)
