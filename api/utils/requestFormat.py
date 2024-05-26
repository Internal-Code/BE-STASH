from pydantic import BaseModel
from api.utils.database.general import localTime

class MoneySpendSchema(BaseModel):
    month: int = localTime().month
    year: int = localTime().year
    category: str
    budget: int

class UpdateCategorySchema(BaseModel):
    month: int = localTime().month
    year: int = localTime().year
    category: str
    changedCategoryInto: str

class DeleteCategorySchema(BaseModel):
    month: int = localTime().month
    year: int = localTime().year
    category: str


class GetSchema(BaseModel):
    month: int = localTime().month
    year: int = localTime().year