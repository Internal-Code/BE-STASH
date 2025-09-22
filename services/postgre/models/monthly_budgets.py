from typing import Optional, ClassVar, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, Integer, ForeignKey
from utils.time_utils import local_time


class MonthlyBudgets(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "monthly_budgets"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False))
    month: int = Field(sa_column=Column(Integer, nullable=False))
    year: int = Field(sa_column=Column(Integer, nullable=False))

    users: Optional["Users"] = Relationship(back_populates="monthly_budgets")
    transactions: List["Transactions"] = Relationship(back_populates="monthly_budgets")
    monthly_budget_categories: List["MonthlyBudgetCategories"] = Relationship(back_populates="monthly_budgets")