from datetime import datetime
from pytz import timezone
from typing import Union
from loguru import logger

async def local_time() -> Union[datetime, None]:
    try:
        time = datetime.now()
    except Exception as E:
        time = None
        logger.error(f"Error while generating local time: {E}")
    return time

async def createCategoryFormat(category: str) -> dict:
    return {
        "createdAt": local_time(),
        "category": category
    }