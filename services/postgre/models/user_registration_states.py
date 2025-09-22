from utils.time_utils import local_time
from typing import Optional, ClassVar, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, Boolean, ForeignKey


class UserRegistrationStates(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "user_registration_states"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False))
    is_email_verified: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    is_phone_number_verified: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    is_pin_created: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))

    users: Optional["Users"] = Relationship(back_populates="user_registration_states")
    otp_requests: List["OtpRequests"] = Relationship(back_populates="user_registration_states")
