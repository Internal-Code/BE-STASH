from fastapi import Query
from src.schema.validator import Validator

validator = Validator()


def validate_phone_number(phone_number: str = Query(...)) -> str:
    return validator.number(data=phone_number, min_length=10, max_length=20)
