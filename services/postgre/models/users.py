from utils.time import local_time
from typing import List, Optional, ClassVar, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from services.postgre.attribute_type import UserDeviceInfoEnum
from sqlalchemy import (
    Enum,
    BigInteger,
    DateTime,
    String,
    CHAR,
    SmallInteger,
)


class Users(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "users"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    country_id: int = Field(sa_column=Column(BigInteger, ForeignKey("countries.id")))
    name: str = Field(sa_column=Column(String(255)))
    email: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    phone_number: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    pin: Optional[str] = Field(default=None, sa_column=Column(CHAR(6), nullable=True))
    device_info: UserDeviceInfoEnum = Field(sa_column=Column(Enum(UserDeviceInfoEnum)))
    user_activated: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))

    countries: Optional["Countries"] = Relationship(back_populates="users")
    user_tokens: List["UserTokens"] = Relationship(back_populates="users")
    user_login_histories: List["UserLoginHistories"] = Relationship(back_populates="users")
    user_registration_states: List["UserRegistrationStates"] = Relationship(back_populates="users")
    pin_resets: List["PinResets"] = Relationship(back_populates="users")
    blacklisted_tokens: List["BlacklistedTokens"] = Relationship(back_populates="users")
    monthly_budgets: List["MonthlyBudgets"] = Relationship(back_populates="users")
    transactions: List["Transactions"] = Relationship(back_populates="users")
