from datetime import datetime
from utils.helper import local_time
from typing import Optional
from enum import StrEnum
from pydantic import BaseModel, Field, EmailStr, field_validator
from src.schema.validator import (
    FullNameValidatorMixin,
    PhoneNumberValidatorMixin,
    SecurityCodeValidator,
    YearValidator,
    UniqueIdValidator,
)


class UserUniqueId(BaseModel):
    unique_id: Optional[str] = None

    @field_validator("unique_id")
    @classmethod
    def validate_unique_id(cls, value: Optional[str]) -> str:
        return UniqueIdValidator.validate_uuid(unique_id=value)


class UserPin(BaseModel):
    pin: Optional[str] = None

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, value: Optional[str]) -> str:
        return SecurityCodeValidator.validate_security_code(value=value, type="pin")


class UserPhoneNumber(BaseModel, PhoneNumberValidatorMixin):
    phone_number: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> str:
        return PhoneNumberValidatorMixin.validate_phone_number(value)


class UserOtp(BaseModel):
    otp: Optional[str] = None

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: Optional[str]) -> str:
        return SecurityCodeValidator.validate_security_code(value=value, type="otp")


class UserEmail(BaseModel):
    email: EmailStr = None


class UserRefreshToken(BaseModel):
    refresh_token: Optional[str] = None


class UserLogin(UserPin, UserUniqueId):
    pass


class UserWrongPhoneNumber(UserPhoneNumber, UserUniqueId):
    pass


class UpdateUserFullName(BaseModel, FullNameValidatorMixin):
    change_full_name_into: Optional[str] = None

    @field_validator("change_full_name_into")
    @classmethod
    def validate_full_name(cls, value: Optional[str]) -> str:
        return FullNameValidatorMixin.validate_fullname(value)


class ChangePin(BaseModel, SecurityCodeValidator):
    current_pin: Optional[str]
    updated_pin: Optional[str]
    confirmed_new_pin: Optional[str]

    @field_validator("current_pin")
    @classmethod
    def validate_current_pin(cls, value: Optional[str]) -> str:
        return SecurityCodeValidator.validate_security_code(value=value, type="pin")

    @field_validator("updated_pin")
    @classmethod
    def validate_updated_pin(cls, value: Optional[str]) -> str:
        return SecurityCodeValidator.validate_security_code(value=value, type="pin")

    @field_validator("confirmed_new_pin")
    @classmethod
    def validate_new_pin(cls, value: Optional[str]) -> str:
        return SecurityCodeValidator.validate_security_code(value=value, type="pin")


class UserResetPin(UserPin, UserUniqueId):
    confirm_new_pin: Optional[str]

    @field_validator("confirm_new_pin")
    @classmethod
    def validate_confirmed_reset_pin(cls, value: Optional[str]) -> str:
        return SecurityCodeValidator.validate_security_code(value=value, type="pin")


class MonthlyCategory(BaseModel):
    category: Optional[str] = None
    budget: int = 100000


class UpdateCategorySchema(BaseModel):
    category: Optional[str] = None
    changed_category_into: Optional[str] = None


class DefaultSchema(BaseModel):
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = local_time().year

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> str:
        return YearValidator.year_must_be_four_digits(value=value)


class UpdateCategorySpending(BaseModel):
    spend_day: int = Field(default=local_time().day, ge=1, le=31)
    changed_spend_day: int = Field(default=local_time().day, ge=1, le=31)
    spend_month: int = Field(default=local_time().month, ge=1, le=12)
    changed_spend_month: int = Field(default=local_time().month, ge=1, le=12)
    spend_year: int = Field(default=local_time().year, ge=1000, le=9999)
    changed_spend_year: int = Field(default=local_time().year, ge=1000, le=9999)
    category: Optional[str]
    changed_category_into: Optional[str]
    description: Optional[str]
    changed_description_into: Optional[str]
    amount: int
    changed_amount_into: int


class DeleteCategorySchema(BaseModel):
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = Field(default=local_time().year, ge=1000, le=9999)
    category: Optional[str]


class CreateSpend(BaseModel):
    day: int = Field(default=local_time().day, ge=1, le=31)
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = Field(default=local_time().year)
    category: Optional[str]
    description: Optional[str]
    amount: int

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> str:
        return YearValidator.year_must_be_four_digits(value=value)


class CreateUser(BaseModel, FullNameValidatorMixin, PhoneNumberValidatorMixin):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_fullname(cls, value: Optional[str]) -> str:
        return FullNameValidatorMixin.validate_fullname(value)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> str:
        return PhoneNumberValidatorMixin.validate_phone_number(value)


class TokenData(BaseModel):
    user_uuid: Optional[str] = None


class DetailUserFullName(BaseModel):
    full_name: Optional[str]


class DetailUserPhoneNumber(BaseModel):
    phone_number: Optional[str]
    verified_phone_number: bool


class DetailUserEmail(BaseModel):
    email: EmailStr | None = None
    verified_email: bool


class UserInDB(CreateUser):
    user_uuid: Optional[str]
    created_at: datetime
    updated_at: datetime | None = None
    full_name: Optional[str] | None = None
    email: EmailStr | None = None
    phone_number: Optional[str] | None = None
    pin: Optional[str] | None = None
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


class SendVerificationLink(UserUniqueId):
    method: SendMethod


class GoogleSSOPayload(BaseModel):
    full_name: Optional[str]
    phone_number: Optional[str]


class SendOTPPayload(BaseModel):
    phoneNumber: Optional[str]
    message: Optional[str]


class ChangeUserPhoneNumber(BaseModel):
    phone_number: Optional[str]


class AddEmail(BaseModel):
    email: EmailStr


class ChangeUserFullName(BaseModel):
    full_name: Optional[str]
