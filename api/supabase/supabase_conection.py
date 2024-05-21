from loguru import logger
from typing import Union
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from api.secret import (
    SUPABASE_DATABASE,
    SUPABASE_HOST,
    SUPABASE_PASSWORD,
    SUPABASE_PORT,
    SUPABASE_USER
)


def database_connection(
    SUPABASE_USER: str = SUPABASE_USER,
    SUPABASE_PASSWORD: str = SUPABASE_PASSWORD,
    SUPABASE_HOST: str = SUPABASE_HOST,
    SUPABASE_PORT: str = SUPABASE_PORT,
    SUPABASE_DATABASE: str = SUPABASE_DATABASE
) -> Union[Engine, None]:

    try:
        engine = create_engine(f"postgresql+psycopg2://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DATABASE}")

        if isinstance(engine, Engine):
            logger.info("Postgre SQL Connected.")
        else:
            logger.info("Error while connecting to Postgre SQL, make sure Postgre SQL account filled correctly.")
            engine = None
    except Exception as E:
        engine = None
        logger.error(f"Error connecting SQL Server: {E}")
    
    return engine