from api.database.databaseConnection import database_connection
from sqlalchemy import (
    MetaData, 
    Table, 
    Column, 
    Integer,
    String,
    DateTime,
    BigInteger,
    
)

meta = MetaData()

money_spend = Table(
    'money_spend', 
    meta, 
    Column('id', Integer, primary_key=True, autoincrement=True), 
    Column('createdAt', DateTime(timezone=True), nullable=False),
    Column('updatedAt', DateTime(timezone=True), nullable=True),
    Column('category', String(255), nullable=False),
    Column('describe', String(255), nullable=False),
    Column('amount', BigInteger, nullable=False),
)

money_spend_schema = Table(
    'money_spend_schema', 
    meta, 
    Column('id', Integer, primary_key=True, autoincrement=True), 
    Column('createdAt', DateTime(timezone=True), nullable=False), 
    Column('updatedAt', DateTime(timezone=True), nullable=True), 
    Column('month', Integer, nullable=False), 
    Column('year', Integer, nullable=False), 
    Column('category', String(255), unique=True, nullable=False),
    Column('budget', BigInteger, nullable=False)
)

async def async_main():
    engine = database_connection()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)