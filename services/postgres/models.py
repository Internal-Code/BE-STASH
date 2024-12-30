from sqlalchemy.dialects.postgresql import UUID
from services.postgres.connection import database_connection
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
    Column("user_uuid", UUID(as_uuid=True), unique=True, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True, default=None),
    Column("full_name", String(255), nullable=True, unique=False, default=None),
    Column("email", String(255), nullable=True, unique=True, default=None),
    Column("phone_number", String(13), nullable=True, unique=False, default=None),
    Column("pin", String(255), nullable=True, unique=False, default=None),
    Column("verified_email", Boolean, nullable=False, default=False),
    Column("verified_phone_number", Boolean, nullable=False, default=False),
)


money_spends = Table(
    "money_spends",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("user_uuid", UUID(as_uuid=True), nullable=False),
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
    Column("user_uuid", UUID(as_uuid=True), nullable=False),
    Column("month", Integer, nullable=False),
    Column("year", Integer, nullable=False),
    Column("category", String(255), nullable=False),
    Column("budget", BigInteger, nullable=False),
)

blacklist_tokens = Table(
    "blacklist_tokens",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("blacklisted_at", DateTime(timezone=True), nullable=False),
    Column("user_uuid", UUID(as_uuid=True), nullable=False),
    Column("access_token", String(255), nullable=False, unique=True),
    Column("refresh_token", String(255), nullable=False, unique=True),
)

user_tokens = Table(
    "user_tokens",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("user_uuid", UUID(as_uuid=True), nullable=False),
    Column("access_token", String(255), nullable=False, unique=True),
    Column("refresh_token", String(255), nullable=False, unique=True),
)

reset_pins = Table(
    "reset_pins",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_uuid", UUID(as_uuid=True), nullable=False, unique=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("email", String(255), nullable=True, unique=False, default=None),
    Column("save_to_hit_at", DateTime(timezone=True), nullable=True, default=None),
    Column("blacklisted_at", DateTime(timezone=True), nullable=True, default=None),
)


send_otps = Table(
    "send_otps",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True, default=None),
    Column("user_uuid", UUID(as_uuid=True), nullable=False),
    Column("otp_number", String(6), nullable=True, default=None),
    Column("current_api_hit", Integer, nullable=True, default=None),
    Column("saved_by_system", Boolean, nullable=False, default=False),
    Column("save_to_hit_at", DateTime(timezone=True), nullable=True, default=None),
    Column("blacklisted_at", DateTime(timezone=True), nullable=True, default=None),
    Column("hit_tomorrow_at", DateTime(timezone=True), nullable=True, default=None),
)


async def database_migration():
    engine = database_connection()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)
