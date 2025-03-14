from datetime import datetime
from typing import Optional
from utils.helper import local_time
from sqlmodel import SQLModel, Field, Relationship
from services.postgres.connection import database_connection


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: int = Field(primary_key=True)
    unique_id: str = Field(unique=True, nullable=False)
    created_at: Optional[datetime] = Field(default=local_time())
    updated_at: Optional[datetime] = Field(default=None, unique=False, nullable=True)
    created_pin_at: Optional[datetime] = Field(default=None, unique=False, nullable=True)
    full_name: Optional[str] = Field(default=None, unique=False, nullable=True)
    email: Optional[str] = Field(default=None, unique=True, nullable=True)
    phone_number: Optional[str] = Field(default=None, unique=True, nullable=True)
    pin: Optional[str] = Field(default=None, unique=False, nullable=True)
    verified_email: bool = Field(default=False)
    verified_phone_number: bool = Field(default=False)
    otp_state: bool = Field(default=False, unique=False, nullable=True)
    register_state: bool = Field(default=False, unique=False, nullable=True)
    money_spend: list["MoneySpend"] = Relationship(back_populates="user", cascade_delete=True)
    monthly_schema: list["MonthlySchema"] = Relationship(back_populates="user", cascade_delete=True)
    category_schema: list["CategorySchema"] = Relationship(back_populates="user", cascade_delete=True)
    blacklist_token: list["BlacklistToken"] = Relationship(back_populates="user", cascade_delete=True)
    user_token: list["UserToken"] = Relationship(back_populates="user", cascade_delete=True)
    reset_pin: list["ResetPin"] = Relationship(back_populates="user", cascade_delete=True)
    send_otp: list["SendOtp"] = Relationship(back_populates="user", cascade_delete=True)


class BlacklistToken(SQLModel, table=True):
    __tablename__ = "blacklist_token"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    access_token: Optional[str] = Field(default=None, unique=True, nullable=True)
    refresh_token: Optional[str] = Field(default=None, unique=True, nullable=True)
    blacklisted_at: datetime = Field(default=local_time())
    user: User = Relationship(back_populates="blacklist_token")


class UserToken(SQLModel, table=True):
    __tablename__ = "user_token"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    created_at: datetime = Field(default=local_time())
    access_token: Optional[str] = Field(default=None, nullable=True)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    user: User = Relationship(back_populates="user_token")


class ResetPin(SQLModel, table=True):
    __tablename__ = "reset_pin"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    created_at: datetime = Field(default=local_time())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    phone_number: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default=None, nullable=True)
    save_to_hit_at: Optional[datetime] = Field(default=None, nullable=True)
    blacklisted_at: Optional[datetime] = Field(default=None, nullable=True)
    user: User = Relationship(back_populates="reset_pin")


class SendOtp(SQLModel, table=True):
    __tablename__ = "send_otp"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    created_at: datetime = Field(default=local_time())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    otp_number: Optional[str] = Field(default=None, nullable=True)
    current_api_hit: Optional[int] = Field(default=None, nullable=True)
    save_to_hit_at: Optional[datetime] = Field(default=None, nullable=True)
    blacklisted_at: Optional[datetime] = Field(default=None, nullable=True)
    user: User = Relationship(back_populates="send_otp")


class MonthlySchema(SQLModel, table=True):
    __tablename__ = "monthly_schema"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    month_id: str = Field(unique=True, nullable=False)
    created_at: Optional[datetime] = Field(default=local_time())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    month: Optional[int] = Field(default=None, nullable=True)
    year: Optional[int] = Field(default=None, nullable=True)
    user: User = Relationship(back_populates="monthly_schema")
    category_schema: list["CategorySchema"] = Relationship(back_populates="monthly_schema", cascade_delete=True)


class CategorySchema(SQLModel, table=True):
    __tablename__ = "category_schema"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    category_id: str = Field(unique=True, nullable=False)
    created_at: datetime = Field(default=local_time())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    month_id: Optional[str] = Field(default=None, foreign_key="monthly_schema.month_id", ondelete="CASCADE")
    category: Optional[str] = Field(default=None, nullable=True)
    budget: Optional[int] = Field(default=None, nullable=True)
    user: User = Relationship(back_populates="category_schema")
    monthly_schema: MonthlySchema = Relationship(back_populates="category_schema")


class MoneySpend(SQLModel, table=True):
    __tablename__ = "money_spend"
    id: int = Field(primary_key=True)
    unique_id: Optional[str] = Field(default=None, foreign_key="user.unique_id", ondelete="CASCADE")
    spend_id: str = Field(unique=True, nullable=False)
    category_id: Optional[str] = Field(default=None, foreign_key="category_schema.category_id", ondelete="CASCADE")
    created_at: datetime = Field(default=local_time())
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    spend_day: Optional[int] = Field(default=None, nullable=True)
    spend_month: Optional[int] = Field(default=None, nullable=True)
    spend_year: Optional[int] = Field(default=None, nullable=True)
    category: Optional[str] = Field(default=None, nullable=True)
    description: Optional[str] = Field(default=None, nullable=True)
    amount: Optional[int] = Field(default=None, nullable=True)
    user: User = Relationship(back_populates="money_spend")


async def database_migration():
    engine = database_connection()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
