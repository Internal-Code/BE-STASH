from typing import Optional, ClassVar, Any, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, Date, String, ForeignKey, Enum
from utils.time_utils import local_time
from services.postgre.attribute_type import TransactionPaymentMethodEnum


class Transactions(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "transactions"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time,sa_column=Column(DateTime, nullable=False))
    updated_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime, nullable=True))
    deleted_at: Optional[datetime] = Field(default=None,sa_column=Column(DateTime, nullable=True))
    transaction_date: date = Field(sa_column=Column(Date, nullable=False))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False),)
    category_id: int = Field(sa_column=Column(BigInteger, ForeignKey("monthly_budget_categories.id"), nullable=False),)
    budget_id: int = Field(sa_column=Column(BigInteger, ForeignKey("monthly_budgets.id"), nullable=False))
    payment_method: TransactionPaymentMethodEnum = Field(sa_column=Column(Enum(TransactionPaymentMethodEnum), nullable=False),)
    total_amount: int = Field(sa_column=Column(BigInteger, nullable=False),)
    description: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True),)

    users: Optional["Users"] = Relationship(back_populates="transactions")
    monthly_budgets: Optional["MonthlyBudgets"] = Relationship(back_populates="transactions")
    monthly_budget_categories: Optional["MonthlyBudgetCategories"] = Relationship(back_populates="transactions")
    transaction_details: List["TransactionDetails"] = Relationship(back_populates="transactions")
