from loguru import logger
from fastapi import APIRouter, status
from api.utils.database.general import checkCategoryAvaibility
from api.models.response import ResponseGeneral
from api.utils.requestFormat import GetSchema
from api.database.databaseConnection import database_connection
from api.database.databaseModel import money_spend_schema

router = APIRouter(tags=["schema"])

async def getSchema(month: int, year: int) -> ResponseGeneral:
    
    response = ResponseGeneral()
    isAvailable = await checkCategoryAvaibility(
        month=month,
        year=year
    )

    try:
        if isAvailable is False:
            response.statusCode = status.HTTP_404_NOT_FOUND
            response.success = False
            response.message = f"Category not found. Please create category first."
        else:
            logger.info("Endpoint get category.")
            async with database_connection().connect() as session:
                async with session.begin():
                    query = money_spend_schema.select()\
                        .where(money_spend_schema.c.month == month)\
                        .where(money_spend_schema.c.year == year)
                    result = await session.execute(query)
                    data = result.fetchall()
                    logger.info(f"Get category {money_spend_schema.name} on {month}/{year}.")
            response.message = "Get schema information success."
            response.body = [dict(row._mapping) for row in data]
    except Exception as E:
        logger.error(f"Error while deleting category: {E}.")
        response.statusCode = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.success = False
        response.message = f"Internal Server Error: {E}."
    
    return response

router.add_api_route(
    methods=["GET"],
    path="/api/v1/get_category", 
    response_model=ResponseGeneral,
    endpoint=getSchema
)