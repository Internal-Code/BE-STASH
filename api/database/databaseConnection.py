from loguru import logger
from typing import Union
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine.base import Engine
from api.secret import (
    LOCAL_POSTGRESQL_DATABASE,
    LOCAL_POSTGRESQL_HOST,
    LOCAL_POSTGRESQL_PASSWORD,
    LOCAL_POSTGRESQL_PORT,
    LOCAL_POSTGRESQL_USER,
    LOCAL_POSTGRESQL_POOL_SIZE,
    LOCAL_POSTGRESQL_MAX_OVERFLOW
)

def database_connection(
    LOCAL_POSTGRESQL_USER: str = LOCAL_POSTGRESQL_USER,
    LOCAL_POSTGRESQL_PASSWORD: str = LOCAL_POSTGRESQL_PASSWORD,
    LOCAL_POSTGRESQL_HOST: str = LOCAL_POSTGRESQL_HOST,
    LOCAL_POSTGRESQL_PORT: str = LOCAL_POSTGRESQL_PORT,
    LOCAL_POSTGRESQL_DATABASE: str = LOCAL_POSTGRESQL_DATABASE,
    LOCAL_POSTGRESQL_POOL_SIZE: int = LOCAL_POSTGRESQL_POOL_SIZE,
    LOCAL_POSTGRESQL_MAX_OVERFLOW: int = LOCAL_POSTGRESQL_MAX_OVERFLOW
) -> Union[Engine, None]:

    engine = None
    
    try:
        engine = create_async_engine(
            f"postgresql+asyncpg://{LOCAL_POSTGRESQL_USER}:{LOCAL_POSTGRESQL_PASSWORD}@{LOCAL_POSTGRESQL_HOST}:{LOCAL_POSTGRESQL_PORT}/{LOCAL_POSTGRESQL_DATABASE}",
            pool_size = LOCAL_POSTGRESQL_POOL_SIZE,
            max_overflow = LOCAL_POSTGRESQL_MAX_OVERFLOW
        )
        
    except Exception as E:
        logger.error(f"Error connecting to PostgreSQL: {E}")
    
    return engine