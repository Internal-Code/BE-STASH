from src.secret import POSTGRE_URL
from sqlalchemy.ext.asyncio import create_async_engine

def database_connection():
    return create_async_engine(url=POSTGRE_URL)

async def get_db():
    async with database_connection().connect() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
