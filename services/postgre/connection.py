from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.secret import POSTGRE_URL

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
