from uuid import uuid4
from typing import Annotated
from utils.logger import logging
from utils.jwt import JWTHandler
from fastapi import APIRouter, status, Depends
from services.postgre.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.model import MonthlySchema
from src.schema.request_format import DefaultSchemaPayload
from src.schema.response import ResponseDefault
from utils.query import QueryDatabase
from utils.error import (
    EntityAlreadyExistError,
    ServiceError,
    StashBaseApiError,
)

jwt_handler = JWTHandler()
router = APIRouter(tags=["Monthly Schema"], prefix="/schema")


async def create_schema_endpoint(
    schema: DefaultSchemaPayload,
    current_user: Annotated[dict, Depends(jwt_handler.get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ResponseDefault:
    logging.info("Create schema endpoint.")
    response = ResponseDefault()
    month_id = str(uuid4())
    query = QueryDatabase(db)

    try:
        monthly_schema_record = await query.find(
            table=MonthlySchema,
            unique_id=current_user.unique_id,
            month=schema.month,
            year=schema.year,
            deleted_at=None,
        )

        if monthly_schema_record:
            logging.error(f"Schema {schema.month}/{schema.year} already exist.")
            raise EntityAlreadyExistError(detail="Schema already exist.")

        await query.insert(
            table=MonthlySchema,
            data={
                "unique_id": current_user.unique_id,
                "month": schema.month,
                "year": schema.year,
                "month_id": month_id,
            },
        )

        response.message = "Schema sucessfully created."

    except StashBaseApiError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")

    return response


router.add_api_route(
    methods=["POST"],
    path="/create",
    response_model=ResponseDefault,
    endpoint=create_schema_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Create budgeting schema for each month.",
)
