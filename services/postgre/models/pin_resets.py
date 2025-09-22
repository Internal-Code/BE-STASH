from utils.time import local_time
from typing import List, Optional, ClassVar, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, String, ForeignKey


class PinResets(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "pin_resets"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True),)
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False))
    ip_address: str = Field(sa_column=Column(String(255), nullable=False))

    users: Optional["Users"] = Relationship(back_populates="pin_resets")
    otp_requests: List["OtpRequests"] = Relationship(back_populates="pin_resets")
