from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field
from src.schema.validator import Validator
from src.schema.enum import OtpRequestTypeEnum
from services.postgre.attribute_type import UserGenderEnum, SendOtpChannelEnum

validator = Validator()


class RegisterUserPayload(BaseModel):
    name: str
    gender: UserGenderEnum
    phone_number: str
    country_id: int = Field(ge=1)
    email: Optional[EmailStr] = Field(default=None)

    @field_validator("phone_number")
    def validate_phone_number(cls, phone_number: str) -> str:
        return validator.number(data=phone_number, min_length=10, max_length=20)

    @field_validator("name")
    def validate_name(cls, name: str) -> str:
        return validator.name(name=name)


class SendOTPPayload(BaseModel):
    phoneNumber: str
    message: str


class VerificationOtpPayload(BaseModel):
    otp_code: str
    user_uid: UUID
    channel: SendOtpChannelEnum = SendOtpChannelEnum.whatsapp
    request_type: OtpRequestTypeEnum = OtpRequestTypeEnum.register_user

    @field_validator("otp_code")
    def validate_otp_code(cls, otp_code: str) -> str:
        return validator.number(data=otp_code, exact_length=6)


class RequestNewOtpPayload(BaseModel):
    user_uid: UUID
    channel: SendOtpChannelEnum = SendOtpChannelEnum.whatsapp
    request_type: OtpRequestTypeEnum = OtpRequestTypeEnum.register_user


class WrongAccountPayload(BaseModel):
    user_uid: UUID
    channel: SendOtpChannelEnum
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    country_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("phone_number")
    def validate_phone_number(cls, phone_number: str) -> str:
        return validator.number(data=phone_number, min_length=10, max_length=20)


class CreatePinPayload(BaseModel):
    user_uid: UUID
    pin: str

    @field_validator("pin")
    def validate_pin(cls, pin: str) -> str:
        return validator.number(data=pin, exact_length=6)
