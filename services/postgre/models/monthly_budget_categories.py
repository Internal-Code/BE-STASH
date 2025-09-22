from typing import Optional, ClassVar, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, String, ForeignKey
from utils.time_utils import local_time


class MonthlyBudgetCategories(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "monthly_budget_categories"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    deleted_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime, nullable=True))
    budget_id: int = Field(sa_column=Column(BigInteger, ForeignKey("monthly_budgets.id"), nullable=False),)
    category_name: str = Field(sa_column=Column(String(255), nullable=False))
    allocated_budget: int = Field(sa_column=Column(BigInteger, nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True),)

    monthly_budgets: Optional["MonthlyBudgets"] = Relationship(back_populates="monthly_budget_categories")
    transactions: List["Transactions"] = Relationship(back_populates="monthly_budget_categories")
