from utils.time import local_time
from typing import Optional, ClassVar, Any
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger, DateTime, CHAR, Enum, ForeignKey
from services.postgre.attribute_type import SendOtpChannelEnum


class OtpRequests(SQLModel, table=True):
    __tablename__: ClassVar[Any] = "otp_requests"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default_factory=local_time, sa_column=Column(DateTime, nullable=False))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    used_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    expired_at: datetime = Field(default_factory=lambda: local_time() + timedelta(minutes=3),sa_column=Column(DateTime, nullable=False))
    registration_state_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("user_registration_states.id"), nullable=True))
    pin_reset_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, ForeignKey("pin_resets.id"), nullable=True))
    otp_code: str = Field(sa_column=Column(CHAR(6), nullable=False))
    channel: SendOtpChannelEnum = Field(sa_column=Column(Enum(SendOtpChannelEnum), nullable=False))

    user_registration_states: Optional["UserRegistrationStates"] = Relationship(back_populates="otp_requests")
    pin_resets: Optional["PinResets"] = Relationship(back_populates="otp_requests")
