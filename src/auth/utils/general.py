from typing import Callable
from fastapi import Request
from fastapi.responses import JSONResponse
from src.auth.utils.logging import logging
from src.auth.routers.exceptions import FinanceTrackerApiError


def create_exception_handler(
    status_code: int, detail_message: str
) -> Callable[[Request, FinanceTrackerApiError], JSONResponse]:
    detail = {"message": detail_message}

    async def exception_handler(
        _: Request, exc: FinanceTrackerApiError
    ) -> JSONResponse:
        if exc:
            detail["message"] = exc.detail

        if exc.name:
            detail["message"] = f"{detail['message']} [{exc.name}]"

        logging.error(exc)
        return JSONResponse(
            status_code=status_code, content={"detail": detail["message"]}
        )

    return exception_handler
