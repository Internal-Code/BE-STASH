from loguru import logger
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from api.utils.database.general import local_time
from api.models.response import ResponseGeneral
from api.database.databaseConnection import database_connection
from api.database.databaseModel import money_spend_category

router = APIRouter(tags=["crud"])

class Category(BaseModel):
    category: str

async def createCategoryFormat(category: str) -> dict:
    return {
        "createdAt": await local_time(),
        "category": category
    }

async def checkCategoryAvaibility(category: str) -> bool:

    try:
        async with database_connection().connect() as session:
            logger.info("Connected PostgreSQL to perform category avaibility validation.")
            query = select(money_spend_category).where(money_spend_category.c.category == category)
            result = await session.execute(query)
            checked = result.scalar_one_or_none()
            if checked:
                result = True
                logger.warning(f"Category {category} already created on table {money_spend_category.name}")
            else:
                result = False
                logger.info(f"Category {category} not found on table {money_spend_category.name}")
    except Exception as E:
        result = False
        logger.error(f"Error while checking category availability: {E}")
    finally:
        await session.close()
        logger.info("PostgreSQL disconected.")
    
    return result

async def createCategory(category: Category) -> ResponseGeneral:
    response = ResponseGeneral()
    prepared_data = await createCategoryFormat(category.category)
    checkingCategory = await checkCategoryAvaibility(category.category)

    if checkingCategory:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Category already exists on database.")

    try:
        logger.info("Endpoint create category.")
        async with database_connection().begin() as connection:
            logger.info("Database PostgreSQL connected.")
            query = money_spend_category.insert().values(prepared_data)
            await connection.execute(query)
            await connection.commit()
            logger.info(f"Inserted data {prepared_data} into table {money_spend_category.name}")
        response.message = "Created new category."
    except Exception as E:
        logger.error(f"Error while creating category: {E}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception error while creating new category: {E}")
    finally:
        await connection.close()
        logger.info("PostgreSQL disconected.")

    return response


router.add_api_route(
    methods=["POST"],
    path="/api/v1/create_category", 
    response_model=ResponseGeneral,
    endpoint=createCategory
)