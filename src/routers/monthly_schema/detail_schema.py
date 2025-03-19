from typing import Annotated
from utils.jwt import JWTHandler
from utils.logger import logging
from utils.query import QueryDatabase
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import MonthlySchema, CategorySchema
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends, Path
from utils.error import ServiceError, StashBaseApiError

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def detail_schema_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year should be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Detail schema endpoint.")
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

        category_schema_entry = await query.find(
            table=CategorySchema,
            fetch="all",
            unique_id=current_user.unique_id,
            month_id=month_id,
            deleted_at=None,
        )

        if not category_schema_entry:
            logging.warning("User is not created category.")
            response.message = "User is not created category."
            return response

        response.message = "Schema successfully fetched."
        response.data = category_schema_entry

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["GET"],
    path="/detail/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=detail_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch schema information on spesific month.",
)
