from uuid import UUID
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

class GetSchema(BaseModel):
    month: int = Field(default=local_time().month, ge=1, le=12)
    year: int = Field(default=local_time().year, ge=1000, le=9999)
    
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
    is_disabled: bool = False
    
class TokenData(BaseModel):
    username: str | None = None
    
class UserInDB(CreateUser):
    id: int
    user_uuid: UUID