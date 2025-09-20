from utils.helper import local_time
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from services.postgre.attribute_type import Environment
from sqlalchemy.dialects.postgresql import (
    ENUM,
    BIGINT,
    VARCHAR,
    INTEGER,
    TIMESTAMP,
    JSON,
)


class ErrorLogs(SQLModel, table=True):
    __tablename__ = "error_logs"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    error_at: datetime = Field(default_factory=local_time, sa_column=Column(TIMESTAMP))
    user_id: int = Field(sa_column=Column(BIGINT, ForeignKey("users.id")))
    raw_error_message: str = Field(sa_column=Column(VARCHAR(255)))
    api_error_message: Optional[str] = Field(
        default=None, sa_column=Column(VARCHAR(255))
    )
    endpoint: str = Field(sa_column=Column(VARCHAR(255)))
    status_code: int = Field(sa_column=Column(INTEGER))
    payload: dict = Field(sa_column=Column(JSON))
    ip_address: str = Field(sa_column=Column(VARCHAR(255)))
    environment: Environment = Field(sa_column=Column(ENUM(Environment)))
    users: Optional["Users"] = Relationship(back_populates="error_logs")
