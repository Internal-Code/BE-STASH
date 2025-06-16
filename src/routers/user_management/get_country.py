from utils.logger import logging
from utils.query import QueryDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from services.postgre.connection import get_db
from services.postgre.models.countries import Countries
from src.schema.response import ResponseDefault
from fastapi import APIRouter, status, Depends
from errors.custom_error import ServiceError, BaseError

router = APIRouter(tags=["User Management"], prefix="/user/management")


async def get_country_endpoint(db: AsyncSession = Depends(get_db)) -> ResponseDefault:
    logging.info("Fetch country data endpdoint.")
    query = QueryDatabase(db)
    response = ResponseDefault()
    errors = {}

    try:
        country_record = await query.find(Countries, fetch="all")

        if not country_record:
            logging.error("Country data not found.")
            errors["country"] = "Country data not found."

        response.message = "Success fetch country data."
        response.data = country_record

    except BaseError:
        raise
    except Exception:
        raise ServiceError(detail="Internal Server Error.", name="STASH")
    return response


router.add_api_route(
    methods=["GET"],
    path="/country",
    response_model=ResponseDefault,
    endpoint=get_country_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Fetch country data.",
)
