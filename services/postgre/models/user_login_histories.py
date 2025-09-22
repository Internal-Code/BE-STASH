from typing import Optional, ClassVar, Any
from datetime import datetime
from utils.time_utils import local_time
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, String, ForeignKey, Numeric


class UserLoginHistories(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "user_login_histories"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    login_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False))
    latitude: Optional[float] = Field(default=None,sa_column=Column(Numeric(9, 6), nullable=True))
    longitude: Optional[float] = Field(default=None,sa_column=Column(Numeric(9, 6), nullable=True))
    ip_address: str = Field(sa_column=Column(String(255), nullable=False))

    users: Optional["Users"] = Relationship(back_populates="user_login_histories")
