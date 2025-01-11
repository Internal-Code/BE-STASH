from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.request_format import DefaultSchema
from utils.helper import local_time
from utils.query.general import find_record, update_record
from services.postgres.models import MonthlySchema
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    EntityAlreadyExistError,
)

router = APIRouter(tags=["Monthly Schema"])


async def update_schema_endpoint(
    month_id: UUID,
    schema: DefaultSchema,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()

    monthly_schema_record = await find_record(
        db=db, table=MonthlySchema, unique_id=current_user.unique_id, month_id=str(month_id), deleted_at=None
    )
    updated_schema_record = await find_record(
        db=db,
        table=MonthlySchema,
        unique_id=current_user.unique_id,
        deleted_at=None,
        month=schema.month,
        year=schema.year,
    )

    try:
        if not monthly_schema_record:
            raise DataNotFoundError(detail="Data not found.")
        if updated_schema_record:
            raise EntityAlreadyExistError(detail=f"Data {schema.month}/{schema.year} already exist.")

        await update_record(
            db=db,
            table=MonthlySchema,
            conditions={
                "month_id": str(month_id),
                "unique_id": current_user.unique_id,
            },
            data={"month": schema.month, "year": schema.year, "updated_at": current_time},
        )

        response.message = "Schema successfully updated."

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/schema/update/{month_id}",
    response_model=ResponseDefault,
    endpoint=update_schema_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Update budgeting schema.",
)
