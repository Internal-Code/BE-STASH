from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import BIGINT, VARCHAR, TIMESTAMP


class ResetPins(SQLModel, table=True):
    __tablename__ = "reset_pins"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    reset_at: datetime = Field(sa_column=Column(TIMESTAMP))
    user_id: int = Field(sa_column=Column(BIGINT, ForeignKey("users.id")))
    ip_address: str = Field(sa_column=Column(VARCHAR(255)))
    send_otps: list["SendOtps"] = Relationship(back_populates="reset_pins")
    users: Optional["Users"] = Relationship(back_populates="reset_pins")
