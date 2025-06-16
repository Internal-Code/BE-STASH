from utils.helper import local_time
from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from services.postgre.attribute_type import DeviceInfo
from sqlalchemy.dialects.postgresql import (
    ENUM,
    BIGINT,
    VARCHAR,
    TIMESTAMP,
    CHAR,
    BOOLEAN,
)


class Users(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default=local_time(), sa_column=Column(TIMESTAMP))
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    country_id: int = Field(sa_column=Column(BIGINT, ForeignKey("countries.id")))
    last_login_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    first_name: str = Field(sa_column=Column(VARCHAR(255)))
    last_name: str = Field(sa_column=Column(VARCHAR(255)))
    email: Optional[str] = Field(
        default=None, sa_column=Column(VARCHAR(255), nullable=True)
    )
    phone_number: Optional[str] = Field(
        default=None, sa_column=Column(VARCHAR(20), nullable=True)
    )
    pin: Optional[str] = Field(default=None, sa_column=Column(CHAR(6), nullable=True))
    device_info: DeviceInfo = Field(
        default=DeviceInfo.android, sa_column=Column(ENUM(DeviceInfo))
    )
    is_account_activated: bool = Field(default=False, sa_column=Column(BOOLEAN))
    countries: Optional["Countries"] = Relationship(back_populates="users")
    register_states: List["RegisterStates"] = Relationship(back_populates="users")
    reset_pins: List["ResetPins"] = Relationship(back_populates="users")
    blacklist_tokens: List["BlacklistTokens"] = Relationship(back_populates="users")
    user_tokens: List["UserTokens"] = Relationship(back_populates="users")
    error_logs: List["ErrorLogs"] = Relationship(back_populates="users")
    monthly_schemas: List["MonthlySchemas"] = Relationship(back_populates="users")
    monthly_categories: List["MonthlyCategories"] = Relationship(back_populates="users")
