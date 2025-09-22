from typing import ClassVar, Any, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, String, Integer, ForeignKey
from utils.time import local_time


class TransactionDetails(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "transaction_details"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    transaction_id: int = Field(sa_column=Column(BigInteger, ForeignKey("transactions.id"), nullable=False))
    item_name: str = Field(sa_column=Column(String(255), nullable=False))
    quantity: int = Field(default=1, sa_column=Column(Integer, nullable=False))
    unit_price: int = Field(sa_column=Column(BigInteger, nullable=False),)
    total_price: int = Field(sa_column=Column(BigInteger, nullable=False))

    transactions: Optional["Transactions"] = Relationship(back_populates="transaction_details")
