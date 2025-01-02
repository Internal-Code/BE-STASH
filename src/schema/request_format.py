from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from utils.helper import local_time
from enum import StrEnum


class MonthlySchema(BaseModel):
    category: str
    budget: int


class UpdateCategorySchema(BaseModel):
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = Field(default=local_time().year, ge=1000, le=9999)
    category: str
    changed_category_into: str


class UpdateCategorySpending(BaseModel):
    spend_day: int = Field(default=local_time().day, ge=1, le=31)
    changed_spend_day: int = Field(default=local_time().day, ge=1, le=31)
    spend_month: int = Field(default=local_time().month, ge=1, le=12)
    changed_spend_month: int = Field(default=local_time().month, ge=1, le=12)
    spend_year: int = Field(default=local_time().year, ge=1000, le=9999)
    changed_spend_year: int = Field(default=local_time().year, ge=1000, le=9999)
    category: str
    changed_category_into: str
    description: str
    changed_description_into: str
    amount: int
    changed_amount_into: int


class DeleteCategorySchema(BaseModel):
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = Field(default=local_time().year, ge=1000, le=9999)
    category: str


class CreateSpend(BaseModel):
    spend_day: int = Field(default=local_time().day, ge=1, le=31)
    spend_month: int = Field(default=local_time().month, ge=1, le=12)
    spend_year: int = Field(default=local_time().year, ge=1000, le=9999)
    category: str
    description: str
    amount: int


class CreateUser(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr | None = None


class UserPin(BaseModel):
    pin: str


class TokenData(BaseModel):
    user_uuid: str = None


class DetailUserFullName(BaseModel):
    full_name: str


class DetailUserPhoneNumber(BaseModel):
    phone_number: str
    verified_phone_number: bool


class DetailUserEmail(BaseModel):
    email: EmailStr | None = None
    verified_email: bool


class UserInDB(CreateUser):
    user_uuid: str
    created_at: datetime
    updated_at: datetime | None = None
    full_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    pin: str | None = None
    verified_email: bool
    verified_phone_number: bool

    def to_detail_user_phone_number(self) -> "DetailUserPhoneNumber":
        return DetailUserPhoneNumber(
            phone_number=self.phone_number,
            verified_phone_number=self.verified_phone_number,
        )

    def to_detail_user_full_name(self) -> "DetailUserFullName":
        return DetailUserFullName(full_name=self.full_name)

    def to_detail_email(self) -> "DetailUserEmail":
        return DetailUserEmail(email=self.email, verified_email=self.verified_email)


class UserForgotPassword(BaseModel):
    email: EmailStr


class SendMethod(StrEnum):
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"


class SendVerificationLink(BaseModel):
    method: SendMethod


class ForgotPin(BaseModel):
    pin: str
    confirm_new_pin: str


class GoogleSSOPayload(BaseModel):
    full_name: str
    phone_number: str


class SendOTPPayload(BaseModel):
    phoneNumber: str
    message: str


class ChangeUserPhoneNumber(BaseModel):
    phone_number: str


class AddEmail(BaseModel):
    email: EmailStr


class ChangePin(BaseModel):
    current_pin: str
    change_pin: str
    confirmed_changed_pin: str


class ChangeUserFullName(BaseModel):
    full_name: str
