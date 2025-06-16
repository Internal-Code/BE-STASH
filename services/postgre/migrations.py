from services.postgre.connection import engine
from sqlmodel import SQLModel


async def database_migration():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
