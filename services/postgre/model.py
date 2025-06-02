from datetime import datetime, timedelta, date
from typing import Optional, List
from utils.helper import local_time
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from services.postgre.connection import engine
from services.postgre.attribute import Environment, Channel, PaymentType


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    country_id: int = Field(foreign_key="country.id")
    last_login_at: Optional[datetime] = Field(default=None, nullable=True)
    first_name: str = Field()
    last_name: str = Field()
    email: Optional[str] = Field(default=None, unique=True, nullable=True)
    phone_number: Optional[str] = Field(default=None, unique=True, nullable=True)
    pin: Optional[str] = Field(default=None, unique=False, nullable=True)
    is_account_activated: bool = Field(default=False)
    country: List["Country"] = Relationship(back_populates="user")
    register_state: List["RegisterState"] = Relationship(back_populates="user")
    reset_pin: List["ResetPin"] = Relationship(back_populates="user")
    blacklist_token: List["BlacklistToken"] = Relationship(back_populates="user")
    user_token: List["UserToken"] = Relationship(back_populates="user")
    error_log: List["ErrorLog"] = Relationship(back_populates="user")
    monthly_schema: List["MonthlySchema"] = Relationship(back_populates="user")
    monthly_category: List["MonthlyCategory"] = Relationship(back_populates="user")


class Country(SQLModel, table=True):
    __tablename__ = "country"
    id: int = Field(primary_key=True)
    name: str = Field()
    iso_code: str = Field()
    dial_code: str = Field()
    flag_url: str = Field()
    user: List[User] = Relationship(back_populates="country")


class RegisterState(SQLModel, table=True):
    __tablename__ = "register_state"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    user_id: int = Field(foreign_key="user.id")
    is_email_verified: bool = Field(default=False)
    is_phone_number_verified: bool = Field(default=False)
    is_pin_created: bool = Field(default=False)
    user: User = Relationship(back_populates="register_state")
    send_otp: list["SendOtp"] = Relationship(back_populates="register_state")


class ResetPin(SQLModel, table=True):
    __tablename__ = "reset_pin"
    id: int = Field(primary_key=True)
    updated_pin_at: datetime = Field()
    user_id: int = Field(foreign_key="user.id")
    ip_address: str = Field()
    send_otp: list["SendOtp"] = Relationship(back_populates="reset_pin")
    user: User = Relationship(back_populates="reset_pin")


class SendOtp(SQLModel, table=True):
    __tablename__ = "send_otp"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    used_at: Optional[datetime] = Field(default=None)
    register_id: Optional[int] = Field(default=None, foreign_key="register_state.id")
    reset_pin_id: Optional[int] = Field(default=None, foreign_key="reset_pin.id")
    otp_code: str = Field()
    expired_at: datetime = Field(
        default_factory=lambda: local_time() + timedelta(minutes=2)
    )
    channel: Channel = Field()
    register_state: RegisterState = Relationship(back_populates="send_otp")
    reset_pin: ResetPin = Relationship(back_populates="send_otp")


class BlacklistToken(SQLModel, table=True):
    __tablename__ = "blacklist_token"
    id: int = Field(primary_key=True)
    blacklisted_at: datetime = Field()
    user_id: int = Field(foreign_key="user.id")
    access_token: str = Field()
    refresh_token: str = Field()
    user: User = Relationship(back_populates="blacklist_token")


class UserToken(SQLModel, table=True):
    __tablename__ = "user_token"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    user_id: int = Field(foreign_key="user.id")
    access_token: str = Field()
    refresh_token: str = Field()
    user: User = Relationship(back_populates="user_token")


class ErrorLog(SQLModel, table=True):
    __tablename__ = "error_log"
    id: int = Field(primary_key=True)
    error_at: datetime = Field(default_factory=local_time)
    user_id: int = Field(foreign_key="user.id")
    raw_error_message: str = Field()
    api_error_message: str = Field()
    endpoint: str = Field()
    status_code: int = Field()
    payload: dict = Field(sa_column=Column(JSON))
    ip_address: str = Field()
    environment: Environment = Field()
    user: User = Relationship(back_populates="error_log")


class MonthlySchema(SQLModel, table=True):
    __tablename__ = "monthly_schema"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    updated_at: datetime = Field()
    user_id: int = Field(foreign_key="user.id")
    start_date: date = Field()
    end_date: date = Field()
    year: int = Field()
    is_deleted: bool = Field(default=False)
    user: User = Relationship(back_populates="monthly_schema")
    monthly_category: List["MonthlyCategory"] = Relationship(
        back_populates="monthly_schema"
    )
    transaction_date: List["TransactionDate"] = Relationship(
        back_populates="monthly_schema"
    )


class MonthlyCategory(SQLModel, table=True):
    __tablename__ = "monthly_category"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    updated_at: datetime = Field()
    user_id: int = Field(foreign_key="user.id")
    schema_id: int = Field(foreign_key="monthly_schema.id")
    category: str = Field()
    budget: float = Field()
    is_deleted: bool = Field(default=False)
    user: User = Relationship(back_populates="monthly_category")
    monthly_schema: MonthlySchema = Relationship(back_populates="monthly_category")
    transaction_date: List["TransactionDate"] = Relationship(
        back_populates="monthly_category"
    )
    transaction_detail: List["TransactionDetail"] = Relationship(
        back_populates="monthly_category"
    )


class TransactionDate(SQLModel, table=True):
    __tablename__ = "transaction_date"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    updated_at: datetime = Field()
    category_id: int = Field(foreign_key="monthly_category.id")
    month_id: int = Field(foreign_key="monthly_schema.id")
    full_date: date = Field()
    is_spend_today: bool = Field(default=True)
    is_deleted: bool = Field(default=False)
    monthly_category: MonthlyCategory = Relationship(back_populates="transaction_date")
    monthly_schema: MonthlySchema = Relationship(back_populates="transaction_date")
    transaction_detail: List["TransactionDetail"] = Relationship(
        back_populates="transaction_date"
    )


class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_method"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    updated_at: datetime = Field()
    payment_type: PaymentType = Field()
    is_deleted: bool = Field(default=False)
    transaction_detail: List["TransactionDetail"] = Relationship(
        back_populates="payment_method"
    )


class TransactionDetail(SQLModel, table=True):
    __tablename__ = "transaction_detail"
    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=local_time)
    updated_at: datetime = Field()
    transaction_date_id: int = Field(foreign_key="transaction_date.id")
    category_id: int = Field(foreign_key="monthly_category.id")
    payment_method_id: int = Field(foreign_key="payment_method.id")
    amount: float = Field()
    description: str = Field()
    is_deleted: bool = Field(default=False)
    transaction_date: TransactionDate = Relationship(
        back_populates="transaction_detail"
    )
    monthly_category: MonthlyCategory = Relationship(
        back_populates="transaction_detail"
    )
    payment_method: PaymentMethod = Relationship(back_populates="transaction_detail")


async def database_migration():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
