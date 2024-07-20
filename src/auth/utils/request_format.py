from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from src.auth.utils.database.general import local_time

class MoneySpendSchema(BaseModel):
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = Field(default=local_time().year, ge=1000, le=9999)
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
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    
class TokenData(BaseModel):
    username: str | None = None
    
class DetailUser(BaseModel):
    user_uuid: UUID
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    
class VerifyUser(BaseModel):
    is_deactivated: bool
    is_verified: bool

    
class UpdatePasswordUser(BaseModel):
    current_password: str
    new_password: str
    retype_new_password: str
    
class UserInDB(CreateUser):
    user_uuid: UUID
    is_deactivated: bool
    is_verified: bool
    
    def to_detail_user(self) -> 'DetailUser':
        return DetailUser(
            user_uuid=self.user_uuid,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            email=self.email
        )
        
    def to_verify_user(self) -> "VerifyUser":
        return VerifyUser(
            is_deactivated=self.is_deactivated,
            is_verified=self.is_verified
        )
        
    def to_update_password_user(self, password_data: UpdatePasswordUser) -> "UpdatePasswordUser":
        return UpdatePasswordUser(
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            retype_new_password=password_data.retype_new_password
        )