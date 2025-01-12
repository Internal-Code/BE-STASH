from uuid import uuid4
from typing import Annotated
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.models import MonthlySchema
from src.schema.response import ResponseDefault, UniqueId
from utils.jwt import get_current_user
from src.schema.request_format import DefaultSchema
from utils.query.general import insert_record, find_record
from utils.custom_error import (
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
)

router = APIRouter(tags=["Monthly Schema"])


async def create_schema_endpoint(
    schema: DefaultSchema,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    month_id = str(uuid4())
    monthly_schema_record = await find_record(
        db=db,
        table=MonthlySchema,
        unique_id=current_user.unique_id,
        month=schema.month,
        year=schema.year,
        deleted_at=None,
    )

    try:
        if monthly_schema_record:
            raise EntityAlreadyExistError(detail=f"Schema {schema.month}/{schema.year} already created.")

        await insert_record(
            db=db,
            table=MonthlySchema,
            data={
                "unique_id": current_user.unique_id,
                "month": schema.month,
                "year": schema.year,
                "month_id": month_id,
            },
        )
        response.message = "Created new schema."
        response.data = UniqueId(unique_id=month_id)

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/schema/create",
    response_model=ResponseDefault,
    endpoint=create_schema_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create budgeting schema for each month.",
)
