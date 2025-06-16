from utils.helper import local_time
from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from services.postgre.attribute_type import PaymentType
from sqlalchemy.dialects.postgresql import ENUM, BIGINT, TIMESTAMP


class PaymentMethods(SQLModel, table=True):
    __tablename__ = "payment_methods"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    payment_type: PaymentType = Field(sa_column=Column(ENUM(PaymentType)))
    transaction_details: List["TransactionDetails"] = Relationship(
        back_populates="payment_methods"
    )
