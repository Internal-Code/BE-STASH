from services.postgre.connection import engine
from services.postgre.attribute import Environment, Channel, PaymentType, DeviceInfo
from utils.helper import local_time
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import (
    BIGINT,
    VARCHAR,
    ENUM,
    INTEGER,
    DATETIME,
    DOUBLE,
    CHAR,
    DATE,
    JSON,
    BOOLEAN,
)


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=(DATETIME))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=(DATETIME), nullable=True
    )
    country_id: int = Field(sa_column=(BIGINT), foreign_key="country.id")
    last_login_at: Optional[datetime] = Field(
        default=None, sa_column=(DATETIME), nullable=True
    )
    first_name: str = Field(sa_column=(VARCHAR(255)))
    last_name: str = Field(sa_column=(VARCHAR(255)))
    email: Optional[str] = Field(default=None, sa_column=(VARCHAR(255)), nullable=True)
    phone_number: Optional[str] = Field(
        default=None, sa_column=(VARCHAR(20)), nullable=True
    )
    pin: Optional[str] = Field(default=None, sa_column=(CHAR(6)), nullable=True)
    device_info: DeviceInfo = Field(
        default=DeviceInfo.ANDROID, sa_column=Column(ENUM(DeviceInfo))
    )
    is_account_activated: bool = Field(default=False, sa_column=(BOOLEAN))

    country: Optional["Country"] = Relationship(back_populates="user")
    register_state: List["RegisterState"] = Relationship(back_populates="user")
    reset_pin: List["ResetPin"] = Relationship(back_populates="user")
    blacklist_token: List["BlacklistToken"] = Relationship(back_populates="user")
    user_token: List["UserToken"] = Relationship(back_populates="user")
    error_log: List["ErrorLog"] = Relationship(back_populates="user")
    monthly_schema: List["MonthlySchema"] = Relationship(back_populates="user")
    monthly_category: List["MonthlyCategory"] = Relationship(back_populates="user")


class Country(SQLModel, table=True):
    __tablename__ = "country"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    name: str = Field(sa_column=Column(VARCHAR(255)))
    iso_code: str = Field(sa_column=Column(VARCHAR(255)))
    dial_code: str = Field(sa_column=Column(VARCHAR(255)))
    flag_url: str = Field(sa_column=Column(VARCHAR(255)))

    user: List["User"] = Relationship(back_populates="country")


class RegisterState(SQLModel, table=True):
    __tablename__ = "register_state"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    user_id: int = Field(foreign_key="user.id", sa_column=Column(BIGINT))
    is_email_verified: bool = Field(default=False, sa_column=(BOOLEAN))
    is_phone_number_verified: bool = Field(default=False, sa_column=(BOOLEAN))
    is_pin_created: bool = Field(default=False, sa_column=(BOOLEAN))

    user: Optional["User"] = Relationship(back_populates="register_state")
    send_otp: list["SendOtp"] = Relationship(back_populates="register_state")


class ResetPin(SQLModel, table=True):
    __tablename__ = "reset_pin"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    reset_at: datetime = Field(sa_column=Column(DATETIME))
    user_id: int = Field(sa_column=Column(BIGINT), foreign_key="user.id")
    ip_address: str = Field(sa_column=Column(VARCHAR(255)))

    send_otp: list["SendOtp"] = Relationship(back_populates="reset_pin")
    user: Optional["User"] = Relationship(back_populates="reset_pin")


class SendOtp(SQLModel, table=True):
    __tablename__ = "send_otp"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    used_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DATETIME), nullable=True
    )
    register_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT),
        foreign_key="register_state.id",
        nullable=True,
    )
    reset_pin_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT),
        foreign_key="reset_pin.id",
        nullable=True,
    )
    otp_code: str = Field(sa_column=Column(CHAR(6)))
    expired_at: datetime = Field(
        default_factory=lambda: local_time() + timedelta(minutes=2),
        sa_column=Column(DATETIME),
    )
    channel: Channel = Field(sa_column=Column(ENUM(Channel)))

    register_state: Optional["RegisterState"] = Relationship(back_populates="send_otp")
    reset_pin: Optional["ResetPin"] = Relationship(back_populates="send_otp")


class BlacklistToken(SQLModel, table=True):
    __tablename__ = "blacklist_token"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    blacklisted_at: datetime = Field(
        default_factory=local_time, sa_column=Column(DATETIME)
    )
    user_id: int = Field(sa_column=Column(BIGINT), foreign_key="user.id")
    access_token: str = Field(sa_column=Column(VARCHAR(255)))
    refresh_token: str = Field(sa_column=Column(VARCHAR(255)))

    user: Optional["User"] = Relationship(back_populates="blacklist_token")


class UserToken(SQLModel, table=True):
    __tablename__ = "user_token"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    user_id: int = Field(sa_column=Column(BIGINT), foreign_key="user.id")
    access_token: str = Field(sa_column=Column(VARCHAR(255)))
    refresh_token: str = Field(sa_column=Column(VARCHAR(255)))

    user: Optional["User"] = Relationship(back_populates="user_token")


class ErrorLog(SQLModel, table=True):
    __tablename__ = "error_log"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    error_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    user_id: int = Field(sa_column=Column(BIGINT), foreign_key="user.id")
    raw_error_message: str = Field(sa_column=Column(VARCHAR(255)))
    api_error_message: Optional[str] = Field(
        default=None, sa_column=Column(VARCHAR(255))
    )
    endpoint: str = Field(sa_column=Column(VARCHAR(255)))
    status_code: int = Field(sa_column=Column(INTEGER))
    payload: dict = Field(sa_column=Column(JSON))
    ip_address: str = Field(sa_column=Column(VARCHAR(255)))
    environment: Environment = Field(sa_column=Column(ENUM(Environment)))

    user: Optional["User"] = Relationship(back_populates="error_log")


class MonthlySchema(SQLModel, table=True):
    __tablename__ = "monthly_schema"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DATETIME), nullable=True
    )
    user_id: int = Field(sa_column=Column(BIGINT), foreign_key="user.id")
    start_date: date = Field(sa_column=Column(DATE))
    end_date: date = Field(sa_column=Column(DATE))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))

    user: Optional["User"] = Relationship(back_populates="monthly_schema")
    monthly_category: List["MonthlyCategory"] = Relationship(
        back_populates="monthly_schema"
    )
    transaction_date: List["TransactionDate"] = Relationship(
        back_populates="monthly_schema"
    )


class MonthlyCategory(SQLModel, table=True):
    __tablename__ = "monthly_category"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DATETIME), nullable=True
    )
    user_id: int = Field(sa_column=Column(BIGINT), foreign_key="user.id")
    schema_id: int = Field(sa_column=Column(BIGINT), foreign_key="monthly_schema.id")
    category: str = Field(sa_column=Column(VARCHAR(255)))
    budget: float = Field(sa_column=Column(DOUBLE))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))

    user: Optional["User"] = Relationship(back_populates="monthly_category")
    monthly_schema: Optional["MonthlySchema"] = Relationship(
        back_populates="monthly_category"
    )
    transaction_date: List["TransactionDate"] = Relationship(
        back_populates="monthly_category"
    )
    transaction_detail: List["TransactionDetail"] = Relationship(
        back_populates="monthly_category"
    )


class TransactionDate(SQLModel, table=True):
    __tablename__ = "transaction_date"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DATETIME), nullable=True
    )
    category_id: int = Field(
        sa_column=Column(BIGINT), foreign_key="monthly_category.id"
    )
    month_id: int = Field(sa_column=Column(BIGINT), foreign_key="monthly_schema.id")
    full_date: date = Field(sa_column=(DATE))
    is_spend_today: bool = Field(default=False, sa_column=(BOOLEAN))
    is_deleted: bool = Field(default=False, sa_column=(BOOLEAN))

    monthly_category: Optional["MonthlyCategory"] = Relationship(
        back_populates="transaction_date"
    )
    monthly_schema: Optional["MonthlySchema"] = Relationship(
        back_populates="transaction_date"
    )
    transaction_detail: Optional["TransactionDetail"] = Relationship(
        back_populates="transaction_date"
    )


class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_method"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DATETIME), nullable=True
    )
    payment_type: PaymentType = Field(sa_column=Column(ENUM(PaymentType)))

    transaction_detail: List["TransactionDetail"] = Relationship(
        back_populates="payment_method"
    )


class TransactionDetail(SQLModel, table=True):
    __tablename__ = "transaction_detail"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DATETIME))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DATETIME), nullable=True
    )
    transaction_date_id: int = Field(
        sa_column=Column(BIGINT), foreign_key="transaction_date.id"
    )
    category_id: int = Field(
        sa_column=Column(BIGINT), foreign_key="monthly_category.id"
    )
    payment_method_id: int = Field(
        sa_column=Column(BIGINT), foreign_key="payment_method.id"
    )
    amount: float = Field(sa_column=Column(DOUBLE))
    description: str = Field(sa_column=Column(VARCHAR(255)))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))

    transaction_date: Optional["TransactionDate"] = Relationship(
        back_populates="transaction_detail"
    )
    monthly_category: Optional["MonthlyCategory"] = Relationship(
        back_populates="transaction_detail"
    )
    payment_method: Optional["PaymentMethod"] = Relationship(
        back_populates="transaction_detail"
    )


async def database_migration():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
