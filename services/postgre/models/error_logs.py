from typing import Optional, ClassVar, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import BigInteger, DateTime, Text, String, JSON, Enum, Integer
from utils.time import local_time
from services.postgre.attribute_type import ErrorLogTypeEnum


class ErrorLogs(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "error_logs"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time,sa_column=Column(DateTime, nullable=False))
    ip_address: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=False))
    type: ErrorLogTypeEnum = Field(sa_column=Column(Enum(ErrorLogTypeEnum), nullable=False))
    status_code: int = Field(sa_column=Column(Integer, nullable=False))
    trace: str = Field(sa_column=Column(Text, nullable=False))
    endpoint: str = Field(sa_column=Column(String(255), nullable=False))
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
