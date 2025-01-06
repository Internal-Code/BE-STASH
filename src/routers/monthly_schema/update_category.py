from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, status, Depends
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from utils.jwt import get_current_user
from services.postgres.models import CategorySchema
from src.schema.request_format import UpdateCategorySchema
from utils.query.general import find_record, update_record
from utils.helper import local_time
from utils.custom_error import (
    EntityAlreadyExistError,
    ServiceError,
    DatabaseQueryError,
    StashBaseApiError,
    DataNotFoundError,
)

router = APIRouter(tags=["Monthly Schema"])


async def update_category_endpoint(
    category_id: UUID,
    schema: UpdateCategorySchema,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    current_time = local_time()

    category_record = await find_record(
        db=db,
        table=CategorySchema,
        category_id=str(category_id),
        category=schema.category,
        unique_id=current_user.unique_id,
        deleted_at=None,
    )

    updated_cagetory_record = await find_record(
        db=db,
        table=CategorySchema,
        unique_id=current_user.unique_id,
        category_id=str(category_id),
        deleted_at=None,
        category=schema.changed_category_into,
    )

    try:
        if not category_record:
            raise DataNotFoundError(detail="Data not found.")
        if updated_cagetory_record:
            raise EntityAlreadyExistError(detail=f"Category {schema.changed_category_into} already exist.")

        await update_record(
            db=db,
            table=CategorySchema,
            conditions={
                "unique_id": current_user.unique_id,
                "category_id": str(category_id),
                "category": schema.category,
            },
            data={"category": schema.changed_category_into, "updated_at": current_time},
        )
        response.message = "Category successfully updated."

    except StashBaseApiError:
        raise
    except DatabaseQueryError:
        raise
    except Exception as E:
        raise ServiceError(detail=f"Service error: {E}.", name="Finance Tracker")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/schema/update-category/{category_id}",
    response_model=ResponseDefault,
    endpoint=update_category_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Update category on spesific schema.",
)
