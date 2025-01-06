from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from utils.helper import local_time
from utils.query.general import find_record, update_record
from services.postgres.models import MonthlySchema
from utils.custom_error import (
    ServiceError,
    DatabaseQueryError,
    StashBaseApiError,
    DataNotFoundError,
)

router = APIRouter(tags=["Monthly Schema"])


async def update_category_schema(
    month_id: UUID, current_user: Annotated[dict, Depends(get_current_user)], db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    current_time = local_time()
    response = ResponseDefault()
    monthly_schema_record = await find_record(
        db=db, table=MonthlySchema, unique_id=current_user.unique_id, month_id=str(month_id), deleted_at=None
    )

    try:
        if not monthly_schema_record:
            raise DataNotFoundError(detail="Data not found.")
        await update_record(
            db=db, table=MonthlySchema, conditions={"month_id": str(month_id)}, data={"deleted_at": current_time}
        )
        response.message = "Data successfully deleted."

    except StashBaseApiError:
        raise
    except DatabaseQueryError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/schema/delete/{month_id}",
    response_model=ResponseDefault,
    endpoint=update_category_schema,
    status_code=status.HTTP_200_OK,
    summary="Delete budgeting schema.",
)
