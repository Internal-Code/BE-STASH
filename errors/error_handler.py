from typing import Any
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from errors.custom_error import BaseError


class CustomError:
    def pydantic_handler(self):
        async def handler(_: Request, exc: Exception) -> JSONResponse:
            if not isinstance(exc, RequestValidationError):
                return JSONResponse(
                    status_code=500,
                    content={"message": "Unexpected error", "error": str(exc)},
                )

            error: dict[str, Any] = {}
            status_code = status.HTTP_400_BAD_REQUEST

            try:
                for err in exc.errors():
                    loc = err.get("loc", [])
                    message = err.get("msg", "Invalid input")

                    if isinstance(loc[-1], int):
                        # malformed JSON
                        error["body"] = f"Malformed JSON: {message}"
                        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                    else:
                        key = loc[-1]
                        error[key] = message

            except Exception as e:
                error["unknown"] = str(e)

            return JSONResponse(
                status_code=status_code,
                content={
                    "message": "Invalid payload request.",
                    "error": error,
                },
            )

        return handler

    def base_handler(self, _: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, BaseError):
            return JSONResponse(
                status_code=exc.status_code,
                content={"message": exc.message, "error": exc.error},
            )

        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error.", "error": str(exc)},
        )
