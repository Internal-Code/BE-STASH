from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from errors.error_handler import CustomError
from errors.custom_error import BaseError

register_error = CustomError()


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(BaseError, register_error.base_handler)
    app.add_exception_handler(RequestValidationError, register_error.pydantic_handler())
