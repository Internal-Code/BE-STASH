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


# class User(SQLModel, table=True):
#     __tablebame__ = "user"
#     id: int = Field(primary_key=True)
#     created_at: datetime = Field(default=local_time())
#     updated_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     unique_id: str|None = Field(default=None, unique=True)
#     full_name: str|None = Field(default=None, unique=False, nullable=True)
#     email: str|None = Field(default=None, unique=True, nullable=True)
#     phone_number: str|None = Field(default=None, unique=True, nullable=True)
#     pin: str|None = Field(default=None, unique=False, nullable=True)
#     verified_email: bool = Field(default=False)
#     verified_phone_number: bool = Field(default=False)
#     money_spend: list["MoneySpend"] = Relationship(back_populates="user", cascade_delete=True)
#     money_spend_schema: list["MoneySpendSchema"] = Relationship(back_populates="user", cascade_delete=True)
#     blacklist_token: list["BlacklistToken"] = Relationship(back_populates="user", cascade_delete=True)
#     user_token: list["UserToken"] = Relationship(back_populates="user", cascade_delete=True)
#     reset_pin: list["ResetPin"] = Relationship(back_populates="user", cascade_delete=True)
#     send_otp: list["SendOtp"] = Relationship(back_populates="user", cascade_delete=True)


# class MoneySpend(SQLModel, table=True):
#     __tablename__ = "money_spend"
#     id: int = Field(primary_key=True)
#     created_at: datetime = Field(default=local_time())
#     updated_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     deleted_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     unique_id: str|None = Field(default=None, unique=False, nullable=False, foreign_key="user.unique_id", ondelete="CASCADE")
#     spend_day: int|None = Field(default=None, unique=False, nullable=True)
#     spend_month: int|None = Field(default=None, unique=False, nullable=True)
#     spend_year: int|None = Field(default=None, unique=False, nullable=True)
#     category: str|None = Field(default=None, unique=False, nullable=True)
#     description: str|None = Field(default=None, unique=False, nullable=True)
#     amount: int|None = Field(default=None,unique=False, nullable=True)
#     user: User = Relationship(back_populates="money_spend")


# class MoneySpendSchema(SQLModel, table=True):
#     __tablename__ = "money_spend_schema"
#     id: int = Field(primary_key=True)
#     created_at: datetime = Field(default=local_time())
#     updated_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     deleted_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     unique_id: str|None = Field(default=None, unique=False, foreign_key="user.unique_id", ondelete="CASCADE")
#     month: int|None = Field(default=None, unique=False, nullable=True)
#     year: int|None = Field(default=None, unique=False, nullable=True)
#     category: str|None = Field(default=None, unique=False, nullable=True)
#     budget: int|None = Field(default=None, unique=False, nullable=True)
#     user: User = Relationship(back_populates="money_spend_schema")

# class BlacklistToken(SQLModel, table=True):
#     __tablename__ = "blacklist_token"
#     id: int = Field(primary_key=True)
#     blacklisted_at: datetime = Field(default=local_time())
#     unique_id: str|None = Field(default=None, unique=False, nullable=False, foreign_key="user.unique_id", ondelete="CASCADE")
#     access_token: str|None = Field(default=None, unique=True, nullable=True)
#     refresh_token: str|None = Field(default=None, unique=True, nullable=True)
#     user: User = Relationship(back_populates="blacklist_token")


# class UserToken(SQLModel, table=True):
#     __tablename__ = "user_token"
#     id: int = Field(primary_key=True)
#     created_at: datetime = Field(default=local_time())
#     unique_id: str|None = Field(default=None, unique=False, nullable=False, foreign_key="user.unique_id", ondelete="CASCADE")
#     access_token: str|None = Field(default=None, unique=True, nullable=True)
#     refresh_token: str|None = Field(default=None, unique=True, nullable=True)
#     user: User = Relationship(back_populates="user_token")

# class ResetPin(SQLModel, table=True):
#     __tablename__ = "reset_pin"
#     id: int = Field(primary_key=True)
#     unique_id: str|None = Field(default=None, unique=False, nullable=False, foreign_key="user.unique_id", ondelete="CASCADE")
#     created_at: datetime = Field(default=local_time())
#     email: str|None = Field(default=None, unique=False, nullable=True)
#     save_to_hit_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     blacklisted_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     user: User = Relationship(back_populates="reset_pin")


# class SendOtp(SQLModel, table=True):
#     __tablename__ = "send_otp"
#     id: int = Field(primary_key=True)
#     created_at: datetime = Field(default=local_time())
#     updated_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     unique_id: str|None = Field(default=None, unique=False, nullable=False, foreign_key="user.unique_id", ondelete="CASCADE")
#     otp_number: str|None = Field(default=None, unique=False, nullable=True)
#     current_api_hit: int|None = Field(default=None, unique=False, nullable=True)
#     saved_by_system: bool = Field(default=False)
#     save_to_hit_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     blacklisted_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     hit_tomorrow_at: datetime|None = Field(default=None, unique=False, nullable=True)
#     user: User = Relationship(back_populates="send_otp")

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
