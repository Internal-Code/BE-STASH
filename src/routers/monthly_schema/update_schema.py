from typing import Annotated
from utils.jwt import JWTHandler
from utils.helper import local_time
from utils.logger import logging
from utils.query import QueryDatabase
from fastapi import APIRouter, status, Depends, Path
from src.schema.response import ResponseDefault
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.request_format import DefaultSchemaPayload
from services.postgres.models import MonthlySchema
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    EntityAlreadyExistError,
    EntityForceInputSameDataError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def update_schema_endpoint(
    schema: DefaultSchemaPayload,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year should be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Update schema endpoint.")
    response = ResponseDefault()
    current_time = local_time()
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
            raise DataNotFoundError(detail="Schema not found.")

        if schema.year == year and schema.month == month:
            logging.error("User force to update into same data.")
            raise EntityForceInputSameDataError(
                detail="Should update into different schema."
            )

        existing_schema_record = await query.find(
            table=MonthlySchema,
            unique_id=current_user.unique_id,
            deleted_at=None,
            month=schema.month,
            year=schema.year,
        )

        if existing_schema_record:
            logging.error(f"Schema {schema.month}/{schema.year} already exist.")
            raise EntityAlreadyExistError(
                detail=f"Schema {schema.month}/{schema.year} already exist."
            )

        await query.update(
            table=MonthlySchema,
            condition={
                "month": month,
                "year": year,
                "unique_id": current_user.unique_id,
            },
            data={
                "month": schema.month,
                "year": schema.year,
                "updated_at": current_time,
            },
        )

        response.message = "Schema successfully updated."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/update/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=update_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Update budgeting schema.",
)
