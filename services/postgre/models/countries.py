from typing import List
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import BIGINT, VARCHAR


class Countries(SQLModel, table=True):
    __tablename__ = "countries"

    id: int = Field(sa_column=Column(BIGINT, primary_key=True, autoincrement=True))
    name: str = Field(sa_column=Column(VARCHAR(255)))
    iso_code: str = Field(sa_column=Column(VARCHAR(255)))
    dial_code: str = Field(sa_column=Column(VARCHAR(255)))
    flag_url: str = Field(sa_column=Column(VARCHAR(255)))
    users: List["Users"] = Relationship(back_populates="countries")
