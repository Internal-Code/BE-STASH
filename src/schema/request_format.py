from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field
from src.schema.validator import Validator

validator = Validator()


class RegisterUserPayload(BaseModel):
    name: str
    phone_number: str
    country_id: int = Field(ge=1)
    email: Optional[EmailStr] = Field(default=None)


class PhoneNumber(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    def validate_phone_number(cls, phone_number: str) -> str:
        return validator.phone_number(phone_number)


class RegisterAccountPayload(PhoneNumber):
    first_name: str
    last_name: str
    country_id: int
    email: Optional[EmailStr]

    @field_validator("first_name")
    def validate_first_name(cls, first_name: str) -> str:
        return validator.name(name=first_name, field="first_name")

    @field_validator("last_name")
    def validate_last_name(cls, last_name: str) -> str:
        return validator.name(name=last_name, field="last_name")


class SendOTPPayload(BaseModel):
    phoneNumber: str
    message: str


# class Email(BaseModel):
#     email: EmailStr = None


# class RefreshToken(BaseModel):
#     refresh_token: str = None


# class RefreshTokenPayload(RefreshToken):
#     pass


# class Pin(BaseModel):
#     pin: str = None

#     @field_validator("pin")
#     @classmethod
#     def validate_pin(cls, value: str) -> str:
#         return SecurityCodeValidator.validate_security_code(value=value, type="pin")


# class UserLoginPayload(Pin):
#     pass


# class CreatePinPayload(Pin):
#     pass


# class Otp(BaseModel):
#     otp: str = None

#     @field_validator("otp")
#     @classmethod
#     def validate_otp(cls, value: str) -> str:
#         return SecurityCodeValidator.validate_security_code(value=value, type="otp")


# class UpdateFullNamePayload(BaseModel):
#     change_full_name_into: str = None

#     @field_validator("change_full_name_into")
#     @classmethod
#     def validate_full_name(cls, value: str) -> str:
#         return FullNameValidatorMixin.validate_fullname(value)


# class UpdatePinPayload(BaseModel):
#     current_pin: str = None
#     updated_pin: str = None
#     confirmed_new_pin: str = None

#     @field_validator("current_pin")
#     @classmethod
#     def validate_current_pin(cls, value: str) -> str:
#         return SecurityCodeValidator.validate_security_code(value=value, type="pin")

#     @field_validator("updated_pin")
#     @classmethod
#     def validate_updated_pin(cls, value: str) -> str:
#         return SecurityCodeValidator.validate_security_code(value=value, type="pin")

#     @field_validator("confirmed_new_pin")
#     @classmethod
#     def validate_new_pin(cls, value: str) -> str:
#         return SecurityCodeValidator.validate_security_code(value=value, type="pin")


# class ResetPinPayload(Pin):
#     confirm_new_pin: str = None

#     @field_validator("confirm_new_pin")
#     @classmethod
#     def validate_confirmed_reset_pin(cls, value: str) -> str:
#         return SecurityCodeValidator.validate_security_code(value=value, type="pin")


# class Category(BaseModel):
#     category: str = None


# class Budget(BaseModel):
#     budget: int = Field(ge=1000)


# class CreateCategoryPayload(Category, Budget):
#     pass


# class UpdateBudgetPayload(Category):
#     changed_budget_into: int = Field(default=local_time().month, ge=1)


# class UpdateCategoryPayload(Category):
#     changed_category_into: str = None


# class Month(BaseModel):
#     month: int = Field(default=local_time().month, ge=1, le=12)


# class Year(BaseModel):
#     year: int = local_time().year

#     @field_validator("year")
#     @classmethod
#     def validate_year(cls, value: int) -> str:
#         return YearValidator.year_must_be_four_digits(value=value)


# class DefaultSchemaPayload(Year, Month):
#     pass


# class Description(BaseModel):
#     description: str = None


# class Amount(BaseModel):
#     amount: int = Field(ge=0)


# class CreateSpendPayload(Description, Category, Amount):
#     pass


# class FullName(BaseModel):
#     first_name: str = None

#     @field_validator("first_name")
#     @classmethod
#     def validate_first_name(cls, value: str) -> str:
#         return FullNameValidatorMixin.validate_name(value)


# class PhoneNumber(BaseModel):
#     phone_number: str = None

#     @field_validator("phone_number")
#     @classmethod
#     def validate_phone_number(cls, value: str) -> str:
#         return PhoneNumberValidatorMixin.validate_phone_number(value)


# class TokenData(BaseModel):
#     user_uuid: str = None


# class DetailUserFullName(BaseModel):
#     full_name: str = None


# class DetailUserPhoneNumber(BaseModel):
#     phone_number: str = None
#     verified_phone_number: bool


# class DetailEmail(BaseModel):
#     email: EmailStr | None = None
#     verified_email: bool


# class UserForgotPassword(BaseModel):
#     email: EmailStr


# class SendMethod(StrEnum):
#     PHONE_NUMBER = "phone_number"
#     EMAIL = "email"


# class SendResetLinkPayload(BaseModel):
#     method: SendMethod


# class ChangeUserPhoneNumber(BaseModel):
#     phone_number: str = None


# class AddEmail(BaseModel):
#     email: EmailStr


# class ChangeUserFullName(BaseModel):
#     full_name: str = None
