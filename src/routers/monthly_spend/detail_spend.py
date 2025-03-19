from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.query import QueryDatabase
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from services.postgres.models import MonthlySchema, MoneySpend
from fastapi import APIRouter, status, Depends, Path
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Spend"], prefix="/spend")


async def detail_spend_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    day: int = Path(ge=1, le=31, description="Day should be between 1 and 31"),
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year should be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Detail spend endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    year = int(year)

    try:
        monthly_schema_entry = await query.find(
            table=MonthlySchema,
            unique_id=current_user.unique_id,
            month=month,
            year=year,
            deleted_at=None,
        )

        if not monthly_schema_entry:
            logging.error(f"Schema {month}/{year} not found.")
            response.message = "Schema not found."
            return response

        month_id = monthly_schema_entry.month_id

        money_spend_entry = await query.find(
            table=MoneySpend,
            fetch="all",
            unique_id=current_user.unique_id,
            month_id=month_id,
            day=day,
            deleted_at=None,
        )

        if not money_spend_entry:
            logging.error("Money spend data is empty.")
            response.message = "Data not found."
            return response

        response.message = "Money spend successfully fetched."
        response.data = money_spend_entry

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/detail/{day}/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=detail_spend_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch schema information on spesific month.",
)
