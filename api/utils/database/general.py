from pytz import timezone
from loguru import logger
from sqlalchemy import select
from datetime import datetime
from sqlalchemy.engine.cursor import CursorResult
from api.database.databaseModel import money_spend_schema
from api.database.databaseConnection import database_connection


def localTime(zone: str = "Asia/Jakarta") -> datetime:
    time = datetime.now(timezone(zone))
    return time

def createCategoryFormat(
    month: int, 
    year: int, 
    category: str, 
    budget: int, 
    updateAt: datetime = None
) -> dict:
    return {
        "createdAt": localTime(),
        "updatedAt": updateAt,
        "month": month,
        "year": year,
        "category": category,
        "budget": budget
    }

async def queryCheckCategory(
    category: str = None,
    month: int = localTime().month,
    year: int = localTime().year
) -> CursorResult | None:
    try:
        async with database_connection().connect() as session:
            logger.info("Connected PostgreSQL to perform category availability validation.")

            if category != None:
                logger.info("Filter with category.")
                query = select(money_spend_schema)\
                .where(money_spend_schema.c.month == month)\
                .where(money_spend_schema.c.year == year)\
                .where(money_spend_schema.c.category == category)
                result = await session.execute(query)
                checked = result.scalar_one_or_none()
            else:
                logger.info("Filter without category.")
                query = select(money_spend_schema)\
                .where(money_spend_schema.c.month == month)\
                .where(money_spend_schema.c.year == year)
                result = await session.execute(query)
                checked = result.fetchone()
    except Exception as E:
        logger.error(f"Error while query check category availability: {E}.")
        checked = None

    return checked

async def checkCategoryAvaibility(
    category: str = None,
    month: int = localTime().month,
    year: int = localTime().year
) -> bool:

    try:
    
        checked = await queryCheckCategory(category, month, year)
        
        if checked and category != None:
            result = True
            logger.warning(f"Category {category} already created on table {money_spend_schema.name}.")
        elif checked and category == None:
            result = True
        else:
            result = False
            logger.info(f"Category {category} not found on table {money_spend_schema.name}.")
    except Exception as E:
        result = False
        logger.error(f"Error while checking category availability: {E}.")
    
    return result