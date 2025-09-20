from utils.helper import local_time
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import BIGINT, VARCHAR, TIMESTAMP


class BlacklistTokens(SQLModel, table=True):
    __tablename__ = "blacklist_tokens"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    blacklisted_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    user_id: int = Field(sa_column=Column(BIGINT, ForeignKey("users.id")))
    access_token: str = Field(sa_column=Column(VARCHAR(255)))
    refresh_token: str = Field(sa_column=Column(VARCHAR(255)))
    users: Optional["Users"] = Relationship(back_populates="blacklist_tokens")
