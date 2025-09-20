from utils.helper import local_time
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import BIGINT, TIMESTAMP, BOOLEAN


class RegisterStates(SQLModel, table=True):
    __tablename__ = "register_states"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    created_at: datetime = Field(default=local_time(), sa_column=Column(TIMESTAMP))
    user_id: int = Field(sa_column=Column(BIGINT, ForeignKey("users.id")))
    is_email_verified: bool = Field(default=False, sa_column=Column(BOOLEAN))
    is_phone_number_verified: bool = Field(default=False, sa_column=Column(BOOLEAN))
    is_pin_created: bool = Field(default=False, sa_column=Column(BOOLEAN))
    users: Optional["Users"] = Relationship(back_populates="register_states")
    send_otps: list["SendOtps"] = Relationship(back_populates="register_states")
