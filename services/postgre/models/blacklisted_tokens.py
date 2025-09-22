from typing import Optional, ClassVar, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, String, ForeignKey
from utils.time_utils import local_time


class BlacklistedTokens(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "blacklisted_tokens"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False))
    access_token: str = Field(sa_column=Column(String(255), nullable=False))
    refresh_token: str = Field(sa_column=Column(String(255), nullable=False))

    users: Optional["Users"] = Relationship(back_populates="blacklisted_tokens")
