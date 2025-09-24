from fastapi import Query
from src.schema.validator import Validator

validator = Validator()


def validate_phone_number(phone_number: str = Query(...)) -> str:
    return validator.phone_number(phone_number)
