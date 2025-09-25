from typing import ClassVar, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, String, Text
from utils.time import local_time


class Countries(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "countries"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    iso_code: str = Field(sa_column=Column(String(255), nullable=False))
    dial_code: str = Field(sa_column=Column(String(255), nullable=False))
    flag_url: str = Field(sa_column=Column(Text, nullable=False))

    users: List["Users"] = Relationship(back_populates="countries")
