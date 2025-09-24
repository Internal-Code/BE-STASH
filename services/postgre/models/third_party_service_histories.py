from typing import ClassVar, Any, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column, Enum
from sqlalchemy import BigInteger, DateTime, String, Integer, ForeignKey, JSON
from utils.time import local_time
from services.postgre.attribute_type import ThirdPartyServiceStatusEnum, ThirdPartyServiceTypeEnum


class ThirdPartyServiceHistories(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "third_party_service_histories"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime))
    user_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False))
    status_code: int = Field(sa_column=Column(Integer, nullable=False))
    type: ThirdPartyServiceTypeEnum = Field(sa_column=Column(Enum(ThirdPartyServiceTypeEnum), nullable=False))
    status: ThirdPartyServiceStatusEnum = Field(sa_column=Column(Enum(ThirdPartyServiceStatusEnum), nullable=False))
    ip_address: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=False))
    recipient: str = Field(sa_column=Column(String(255), nullable=False))
    response_message: dict[str,Any] = Field(default=None,sa_column=Column(JSON, nullable=False))
    
    users: Optional["Users"] = Relationship(back_populates="third_party_service_histories")