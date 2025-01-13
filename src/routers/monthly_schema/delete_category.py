from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, status, Depends
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgres.connection import get_db
from src.schema.request_format import MonthlyCategory
from utils.helper import local_time
from utils.query.general import find_record, update_record
from services.postgres.models import CategorySchema
from utils.custom_error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
)

router = APIRouter(tags=["Monthly Schema"])


async def update_category_endpoint(
    category_id: UUID,
    schema: MonthlyCategory,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    current_time = local_time()
    response = ResponseDefault()
    category_record = await find_record(
        db=db,
        table=CategorySchema,
        unique_id=current_user.unique_id,
        category_id=str(category_id),
        deleted_at=None,
        category=schema.category,
        budget=schema.budget,
    )

    try:
        if not category_record:
            raise DataNotFoundError(detail="Data not found.")
        await update_record(
            db=db,
            table=CategorySchema,
            conditions={
                "unique_id": current_user.unique_id,
                "category": schema.category,
                "budget": schema.budget,
                "category_id": str(category_id),
            },
            data={"deleted_at": current_time},
        )
        response.message = "Data successfully deleted."

    except StashBaseApiError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/schema/delete-category/{category_id}",
    response_model=ResponseDefault,
    endpoint=update_category_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Delete category in spesific schema.",
)
