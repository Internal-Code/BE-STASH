from utils.helper import local_time
from typing import List, Optional
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


class MonthlyCategories(SQLModel, table=True):
    __tablename__ = "monthly_categories"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    user_id: int = Field(sa_column=Column(BIGINT, ForeignKey("users.id")))
    schema_id: int = Field(sa_column=Column(BIGINT, ForeignKey("monthly_schemas.id")))
    category: str = Field(sa_column=Column(VARCHAR(255)))
    budget: float = Field(sa_column=Column(DOUBLE_PRECISION))
    is_deleted: bool = Field(default=False, sa_column=Column(BOOLEAN))
    users: Optional["Users"] = Relationship(back_populates="monthly_categories")
    monthly_schemas: Optional["MonthlySchemas"] = Relationship(
        back_populates="monthly_categories"
    )
    transaction_dates: List["TransactionDates"] = Relationship(
        back_populates="monthly_categories"
    )
    transaction_details: List["TransactionDetails"] = Relationship(
        back_populates="monthly_categories"
    )
