from typing import Annotated
from utils.logger import logging
from utils.jwt import JWTHandler
from utils.query import QueryDatabase
from utils.helper import local_time
from fastapi import APIRouter, status, Depends, Path
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from src.schema.request_format import Category
from services.postgre.model import CategorySchema, MonthlySchema
from utils.error import (
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Category"], prefix="/category")


async def delete_category_endpoint(
    schema: Category,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex=r"^\d{4}$", description="Year should be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Delete category endpoint.")
    response = ResponseDefault()
    query = QueryDatabase(db)
    year = int(year)
    current_time = local_time()

    try:
        monthly_schema_record = await query.find(
            table=MonthlySchema, month=month, year=year, deleted_at=None
        )

        if not monthly_schema_record:
            logging.error(f"Schema {month}/{year} not found.")
            raise DataNotFoundError(detail="Schema not found.")

        category_record = await query.find(
            table=CategorySchema,
            unique_id=current_user.unique_id,
            category=schema.category,
            deleted_at=None,
        )

        if not category_record:
            logging.error(f"Category {schema.category} not found.")
            raise DataNotFoundError(detail="Category not found.")

        category_id = category_record.category_id

        await query.update(
            table=CategorySchema,
            condition={"category_id": category_id},
            data={"deleted_at": current_time},
        )

        response.message = "Category successfully deleted."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/delete/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=delete_category_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Delete spesific category.",
)
