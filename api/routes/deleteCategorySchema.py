from loguru import logger
from fastapi import APIRouter, status
from api.utils.database.general import checkCategoryAvaibility
from api.models.response import ResponseDefault
from api.utils.requestFormat import DeleteCategorySchema
from api.database.databaseConnection import database_connection
from api.database.databaseModel import money_spend_schema

router = APIRouter(tags=["schema"])

async def updateCategorySchema(schema: DeleteCategorySchema) -> ResponseDefault:
    
    response = ResponseDefault()
    isAvailable = await checkCategoryAvaibility(
        month=schema.month,
        year=schema.year,
        category=schema.category
    )

    try:
        if isAvailable is False:
            response.statusCode = status.HTTP_404_NOT_FOUND
            response.success = False
            response.message = f"Category {schema.category} not found. Please create category first."
        else:
            logger.info("Endpoint delete category.")
            async with database_connection().connect() as session:
                async with session.begin():
                    query = money_spend_schema.delete()\
                        .where(money_spend_schema.c.month == schema.month)\
                        .where(money_spend_schema.c.year == schema.year)\
                        .where(money_spend_schema.c.category == schema.category)
                    await session.execute(query)
                    await session.commit()
                    logger.info(f"Deleted category {schema.category}.")
            response.message = "Delete category success."
    except Exception as E:
        logger.error(f"Error while deleting category: {E}.")
        response.statusCode = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.success = False
        response.message = f"Internal Server Error: {E}."
    
    return response

router.add_api_route(
    methods=["DELETE"],
    path="/api/v1/delete_category", 
    response_model=ResponseDefault,
    endpoint=updateCategorySchema
)