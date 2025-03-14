from uuid import UUID
from typing import Annotated
from utils.logger import logging
from fastapi import APIRouter, status, Depends, Path
from services.postgres.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.response import ResponseDefault
from utils.jwt import JWTHandler
from src.schema.request_format import MonthlyCategory
from utils.query import QueryDatabase
from services.postgres.models import (
    CategorySchema,
    MonthlySchema,
    UserToken,
    BlacklistToken,
)
from utils.error import (
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
    DataNotFoundError,
    InvalidTokenError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"])


async def create_category_endpoint(
    schema: MonthlyCategory,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    month: int = Path(ge=1, le=12, description="Month should be between 1 and 12"),
    year: str = Path(regex="^\d{4}$", description="Year must be exactly 4 digits"),
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    response = ResponseDefault()
    query = QueryDatabase(db)
    year = int(year)
    
    monthly_schema_record = await query.find(
        table=MonthlySchema,
        month = month,
        year = year,
        deleted_at = None
    )
    
    category_record = await query.find(
        table=CategorySchema,
        unique_id=current_user.unique_id,
        category=schema.category,
        category_id=str(month_id),
        deleted_at=None,
    )
    monthly_schema_record = await query.find(
        table=MonthlySchema, month_id=str(month_id)
    )
    
    try:
        if not monthly_schema_record:
            logging.info("Schema not found.")
            raise DataNotFoundError(detail="Schema not found.")

        month_id = monthly_schema_record.month_id
        
        if category_record:
            logging.info(f"Category {schema.category} already created.")
            raise EntityAlreadyExistError(detail=f"Category {schema.category} already created.")

        await query.insert(
            table=CategorySchema,
            data={
                "category": schema.category,
                "budget": schema.budget,
                "category_id": str(month_id),
                "unique_id": current_user.unique_id,
            },
        )
        response.message = "Created new category."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/create/category/{month}/{year}",
    response_model=ResponseDefault,
    endpoint=create_category_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create category for each month.",
)
