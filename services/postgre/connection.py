from src.secret import POSTGRE_URL
from sqlmodel import SQLModel
from utils.logger import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(POSTGRE_URL)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def drop_database():
    logging.info("Teardown database.")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    logging.info("Database dropped successfully.")


async def migrate_database():
    logging.info("Migrating table.")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logging.info("Database migration completed successfully.")
