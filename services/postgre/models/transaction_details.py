from utils.helper import local_time
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import (
    BIGINT,
    VARCHAR,
    TIMESTAMP,
    DOUBLE_PRECISION,
    BOOLEAN,
)


class TransactionDetails(SQLModel, table=True):
    __tablename__ = "transaction_details"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    transaction_date_id: int = Field(
        sa_column=Column(BIGINT, ForeignKey("transaction_dates.id"))
    )
    category_id: int = Field(
        sa_column=Column(BIGINT, ForeignKey("monthly_categories.id"))
    )
    payment_method_id: int = Field(
        sa_column=Column(BIGINT, ForeignKey("payment_methods.id"))
    )
    amount: float = Field(sa_column=Column(DOUBLE_PRECISION))
    description: str = Field(sa_column=Column(VARCHAR(255)))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))
    transaction_dates: Optional["TransactionDates"] = Relationship(
        back_populates="transaction_details"
    )
    monthly_categories: Optional["MonthlyCategories"] = Relationship(
        back_populates="transaction_details"
    )
    payment_methods: Optional["PaymentMethods"] = Relationship(
        back_populates="transaction_details"
    )
