from api.database.databaseConnection import database_connection
from sqlalchemy import (
    MetaData, 
    Table, 
    Column, 
    Integer,
    String,
    DateTime,
    Float
)

meta = MetaData()

money_spend = Table(
    'money_spend', 
    meta, 
    Column('id', Integer, primary_key=True, autoincrement=True), 
    Column('createdAt', DateTime, nullable=False), 
    Column('category', String(255), nullable=False),
    Column('describe', String(255), nullable=False),
    Column('amount', Float, nullable=False),
)

money_spend_category = Table(
    'money_spend_category', 
    meta, 
    Column('id', Integer, primary_key=True, autoincrement=True), 
    Column('createdAt', DateTime, nullable=False), 
    Column('category', String(255), unique=True, nullable=False)
)

async def async_main():
    engine = database_connection()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)