from typing import Annotated
from utils.logger import logging
from utils.jwt import JWTHandler
from utils.time import local_time
from utils.query import QueryDatabase
from fastapi import APIRouter, status, Depends, Path
from src.schema.response import ResponseDefault
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.model import MonthlySchema
from utils.error import (
    ServiceError,
    StashBaseApiError,
    NotFoundError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def delete_schema_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex=r"^\d{4}$", description="Year should be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Delete schema endpoint.")
    current_time = local_time()
    response = ResponseDefault()
    query = QueryDatabase(db)
    year = int(year)

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
            raise NotFoundError(detail="Schema not found.")

        await query.update(
            table=MonthlySchema,
            condition={"month": month, "year": year},
            data={"deleted_at": current_time},
        )

        response.message = "Schema successfully deleted."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/delete/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=delete_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Delete budgeting schema.",
)
