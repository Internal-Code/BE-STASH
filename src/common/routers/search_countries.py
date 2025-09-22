import traceback
from src.schema.response import BaseResponse
from utils.logger import logging
from fastapi import APIRouter, status, Depends, Query, HTTPException
from typing import Optional, Any, cast
from errors.custom_error import BaseError
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from services.postgre.query_schema import SelectData, Filters
from services.postgre.query import DatabaseQuery
from services.postgre.connection import get_db
from services.postgre.models import Countries


router = APIRouter(tags=["Countries"], prefix="/countries")


async def search_countries_endpoint(
    name: Optional[str] = Query(default=None, description="Filter country by name"),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """
    Search countries by name prefix (case-insensitive).
    Only countries whose names start with the given string are returned.
    """

    response = BaseResponse()
    session = DatabaseQuery(db)
    try:
        logging.info(f"Searching countries with name filter: {name}")
        c = aliased(Countries)
        c_select = SelectData(
            entry=[
                cast(ColumnElement[Any], c.id).label("id"),
                cast(ColumnElement[Any], c.name).label("name"),
                cast(ColumnElement[Any], c.dial_code).label("dial_code"),
            ]
        )

        c_filter: Optional[Filters] = None

        if name:
            logging.info(f"Filter country name: {name}")
            c_filter = Filters(
                filters=[
                    Filters(
                        field_name=func.lower(c.name),
                        filter_type="like",
                        value=f"{name.lower()}%",
                    )
                ]
            )

        c_data: Any = await session.fetch(
            field_names=c_select,
            master_table=c,
            filters=c_filter,
        )

        response.message = "Success fetch country data."
        response.data = c_data

    except BaseError:
        raise
    except Exception as e:
        logging.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

    return response


router.add_api_route(
    methods=["GET"],
    path="/search",
    endpoint=search_countries_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Search countries by name.",
    response_model=BaseResponse,
)
