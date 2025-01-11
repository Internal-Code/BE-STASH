from uuid import UUID
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from services.postgres.models import CategorySchema, MonthlySchema
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from utils.query.general import find_record
from utils.custom_error import ServiceError, StashBaseApiError, DataNotFoundError

router = APIRouter(tags=["Monthly Schema"])


async def list_category_endpoint(
    month_id: UUID, current_user: Annotated[dict, Depends(get_current_user)], db: AsyncSession = Depends(get_db)
) -> ResponseDefault:
    response = ResponseDefault()
    month_entry = await find_record(
        db=db,
        table=MonthlySchema,
        fetch_type="all",
        unique_id=current_user.unique_id,
        month_id=str(month_id),
        deleted_at=None,
    )
    category_entries = await find_record(
        db=db,
        table=CategorySchema,
        fetch_type="all",
        unique_id=current_user.unique_id,
        category_id=str(month_id),
        deleted_at=None,
    )

    try:
        if not month_entry:
            raise DataNotFoundError(detail="Data not found.")
        if category_entries:
            response.message = f"Fetched {len(category_entries)} data."
            response.data = category_entries
            return response

        response.message = "No category data available."

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["GET"],
    path="/schema/list-category/{month_id}",
    response_model=ResponseDefault,
    endpoint=list_category_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch all category information.",
)
