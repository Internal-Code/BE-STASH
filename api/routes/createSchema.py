from loguru import logger
from fastapi import APIRouter, status
from api.utils.database.general import createCategoryFormat, checkCategoryAvaibility
from api.models.response import ResponseDefault
from api.utils.requestFormat import MoneySpendSchema
from api.database.databaseConnection import database_connection
from api.database.databaseModel import money_spend_schema

router = APIRouter(tags=["schema"])

async def createSchema(schema: MoneySpendSchema) -> ResponseDefault:
    
    response = ResponseDefault()
    isAvailable = await checkCategoryAvaibility(
        month=schema.month,
        year=schema.year,
        category=schema.category
    )
    preparedData = createCategoryFormat(
        month=schema.month, 
        year=schema.year, 
        category=schema.category, 
        budget=schema.budget
    )

    try:
        if isAvailable is True:
            response.statusCode = status.HTTP_403_FORBIDDEN
            response.success = False
            response.message = f"Category {schema.category} already saved."
        else:
            logger.info("Endpoint create category.")
            async with database_connection().connect() as session:
                async with session.begin():
                    query = money_spend_schema.insert().values(preparedData)
                    await session.execute(query)
                    await session.commit()
                    logger.info(f"Created new category: {schema.category}.")
            response.message = "Created new category."
    except Exception as E:
        logger.error(f"Error while creating category: {E}.")
        response.statusCode = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.success = False
        response.message = f"Internal Server Error: {E}."
    
    return response

router.add_api_route(
    methods=["POST"],
    path="/api/v1/create_schema", 
    response_model=ResponseDefault,
    endpoint=createSchema
)