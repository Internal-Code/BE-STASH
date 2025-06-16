from utils.helper import local_time
from typing import List, Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import (
    BIGINT,
    TIMESTAMP,
    DATE,
    BOOLEAN,
)


class MonthlySchemas(SQLModel, table=True):
    __tablename__ = "monthly_schemas"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    user_id: int = Field(sa_column=Column(BIGINT, ForeignKey("users.id")))
    start_date: date = Field(sa_column=Column(DATE))
    end_date: date = Field(sa_column=Column(DATE))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))
    users: Optional["Users"] = Relationship(back_populates="monthly_schemas")
    monthly_categories: List["MonthlyCategories"] = Relationship(
        back_populates="monthly_schemas"
    )
    transaction_dates: List["TransactionDates"] = Relationship(
        back_populates="monthly_schemas"
    )
