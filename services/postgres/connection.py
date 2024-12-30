from src.secret import Config
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine


config = Config()


def database_connection(POSTGRES_URL: str = config.POSTGRES_URL) -> AsyncEngine:
    engine = create_async_engine(url=POSTGRES_URL)
    return engine
