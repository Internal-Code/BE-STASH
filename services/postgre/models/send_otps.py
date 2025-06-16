from utils.helper import local_time
from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from services.postgre.attribute_type import Channel
from sqlalchemy.dialects.postgresql import (
    ENUM,
    BIGINT,
    TIMESTAMP,
    CHAR,
)


class SendOtps(SQLModel, table=True):
    __tablename__ = "send_otps"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        default_factory=local_time, sa_column=Column(TIMESTAMP)
    )
    used_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, nullable=True)
    )
    register_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT, ForeignKey("register_states.id"), nullable=True),
    )
    reset_pin_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT, ForeignKey("reset_pins.id"), nullable=True),
    )
    otp_code: str = Field(sa_column=Column(CHAR(6)))
    expired_at: datetime = Field(
        default_factory=lambda: local_time() + timedelta(minutes=2),
        sa_column=Column(TIMESTAMP),
    )
    channel: Channel = Field(sa_column=Column(ENUM(Channel)))
    register_states: Optional["RegisterStates"] = Relationship(
        back_populates="send_otps"
    )
    reset_pins: Optional["ResetPins"] = Relationship(back_populates="send_otps")
