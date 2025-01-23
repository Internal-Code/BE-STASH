from src.secret import Config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession


config = Config()


def database_connection(POSTGRES_URL: str = config.POSTGRES_URL) -> AsyncEngine:
    engine = create_async_engine(url=POSTGRES_URL)
    return engine


async def get_db() -> AsyncSession:
    async with database_connection().connect() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
