from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field
from src.schema.validator import Validator
from services.postgre.attribute_type import UserGenderEnum

validator = Validator()


class RegisterUserPayload(BaseModel):
    name: str
    gender: UserGenderEnum
    phone_number: str
    country_id: int = Field(ge=1)
    email: Optional[EmailStr] = Field(default=None)

    @field_validator("phone_number")
    def validate_phone_number(cls, phone_number: str) -> str:
        return validator.phone_number(phone_number=phone_number)

    @field_validator("name")
    def validate_name(cls, name: str) -> str:
        return validator.name(name=name)


class SendOTPPayload(BaseModel):
    phoneNumber: str
    message: str
