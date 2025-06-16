from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from errors.custom_error import QueryError, NotFoundError, BaseError
from errors.error_handler import base_error_handler, pydantic_payload_handler


def custom_error_handler(app: FastAPI):
    app.add_exception_handler(QueryError, base_error_handler)
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(NotFoundError, base_error_handler)
    app.add_exception_handler(RequestValidationError, pydantic_payload_handler())
