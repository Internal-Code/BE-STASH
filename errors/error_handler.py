from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from errors.custom_error import BaseError
from utils.logger import logging


def pydantic_payload_handler():
    async def handler(_: Request, exception: RequestValidationError):
        errors = {}
        status_code = status.HTTP_400_BAD_REQUEST

        try:
            for err in exception.errors():
                loc = err.get("loc", [])
                message = err.get("msg", "Invalid input")

                if isinstance(loc[-1], int):
                    errors["body"] = f"Malformed JSON: {message}"
                    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                else:
                    key = loc[-1]
                    errors[key] = message

        except Exception as e:
            errors["unknown"] = str(e)

        logging.error(f"Pydantic handler: {exception}")
        return JSONResponse(
            status_code=status_code,
            content={"message": "Invalid payload request.", "errors": errors},
        )

    return handler


def base_error_handler(_: Request, exception: BaseError):
    logging.error(f"Error message: {exception.message}")
    logging.error(f"Error detail: {exception.errors}")
    return JSONResponse(
        status_code=exception.status_code,
        content={"message": exception.message, "errors": exception.errors},
    )
