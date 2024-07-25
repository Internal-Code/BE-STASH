from uuid_extensions import uuid7
from sqlalchemy.dialects.postgresql import UUID
from src.database.connection import database_connection
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    BigInteger,
    Boolean,
)

meta = MetaData()

users = Table(
    "users",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_uuid", UUID(as_uuid=True), default=uuid7, unique=True, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("username", String(255), nullable=False, unique=True),
    Column("first_name", String(255), nullable=False, unique=False),
    Column("last_name", String(255), nullable=False, unique=False),
    Column("email", String(255), nullable=False, unique=True),
    Column("verified_at", DateTime(timezone=True), nullable=True, default=None),
    Column("password", String(255), nullable=False),
    Column("is_deactivated", Boolean, nullable=False, default=False),
    Column("last_login", DateTime(timezone=True), nullable=True),
)

money_spends = Table(
    "money_spends",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("user_uuid", UUID(as_uuid=True), default=uuid7, nullable=False),
    Column("spend_day", Integer, nullable=False),
    Column("spend_month", Integer, nullable=False),
    Column("spend_year", Integer, nullable=False),
    Column("category", String(255), nullable=False),
    Column("description", String(255), nullable=False),
    Column("amount", BigInteger, nullable=False),
)

money_spend_schemas = Table(
    "money_spend_schemas",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("user_uuid", UUID(as_uuid=True), default=uuid7, nullable=False),
    Column("month", Integer, nullable=False),
    Column("year", Integer, nullable=False),
    Column("category", String(255), nullable=False),
    Column("budget", BigInteger, nullable=False),
)


async def async_main():
    engine = database_connection()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)
