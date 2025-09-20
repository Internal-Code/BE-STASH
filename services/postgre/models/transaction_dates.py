from utils.helper import local_time
from typing import Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import (
    BIGINT,
    TIMESTAMP,
    DATE,
    BOOLEAN,
)


class TransactionDates(SQLModel, table=True):
    __tablename__ = "transaction_dates"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    category_id: int = Field(
        sa_column=Column(BIGINT, ForeignKey("monthly_categories.id"))
    )
    month_id: int = Field(sa_column=Column(BIGINT, ForeignKey("monthly_schemas.id")))
    full_date: date = Field(sa_column=Column(DATE))
    is_spend_today: bool = Field(default=False, sa_column=Column(BOOLEAN))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))
    monthly_categories: Optional["MonthlyCategories"] = Relationship(
        back_populates="transaction_dates"
    )
    monthly_schemas: Optional["MonthlySchemas"] = Relationship(
        back_populates="transaction_dates"
    )
    transaction_details: Optional["TransactionDetails"] = Relationship(
        back_populates="transaction_dates"
    )
