from utils.time import local_time
from typing import ClassVar, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import BigInteger, DateTime, Enum
from services.postgre.attribute_type import RoleNameEnum


class Roles(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "roles"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime))
    name: RoleNameEnum = Field(sa_column=Column(Enum(RoleNameEnum), nullable=False))

    user_tokens: List["UserTokens"] = Relationship(back_populates="roles")
