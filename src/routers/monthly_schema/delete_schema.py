from typing import Annotated
from fastapi import APIRouter, status, Depends, Path
from src.schema.response import ResponseDefault
from utils.jwt import JWTHandler
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.helper import local_time
from utils.query import QueryDatabase
from services.postgres.models import MonthlySchema
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def delete_schema_endpoint(
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year must be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    current_time = local_time()
    response = ResponseDefault()
    query = QueryDatabase(db)
    year = int(year)

    monthly_schema_record = await query.find(
        table=MonthlySchema,
        unique_id=current_user.unique_id,
        month=month,
        year=year,
        deleted_at=None,
    )

    try:
        if not monthly_schema_record:
            raise DataNotFoundError(detail="Data not found.")
        await query.update(
            table=MonthlySchema,
            condition={"month": month, "year": year},
            data={"deleted_at": current_time},
        )
        response.message = "Sucess deleted data."

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
