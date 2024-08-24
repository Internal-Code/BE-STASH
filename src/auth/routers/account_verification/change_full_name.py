from typing import Annotated
from src.database.models import users
from src.auth.utils.logging import logging
from src.auth.schema.response import ResponseDefault
from src.database.connection import database_connection
from fastapi import APIRouter, status, Depends, HTTPException
from src.auth.utils.database.general import local_time, check_fullname
from src.auth.utils.request_format import ChangeUserFullName
from src.auth.utils.jwt.general import get_current_user

router = APIRouter(tags=["account-verification"], prefix="/change")


async def change_full_name_endpoint(
    schema: ChangeUserFullName, current_user: Annotated[dict, Depends(get_current_user)]
) -> ResponseDefault:
    response = ResponseDefault()
    validated_full_name = await check_fullname(value=schema.full_name)

    try:
        async with database_connection().connect() as session:
            try:
                query = (
                    users.update()
                    .where(users.c.user_uuid == current_user.user_uuid)
                    .values(updated_at=local_time(), full_name=validated_full_name)
                )

                await session.execute(query)
                await session.commit()
                logging.info("Success changed user full name.")
            except HTTPException as E:
                raise E
            except Exception as E:
                logging.error(f"Error while change user full name: {E}.")
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal Server Error: {E}.",
                )
            finally:
                await session.close()

        response.success = True
        response.message = "User successfully changed full name."

    except HTTPException as e:
        raise e

    except Exception as E:
        logging.error(f"Error after change_pin_endpoint: {E}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {E}.",
        )
    return response


router.add_api_route(
    methods=["PATCH"],
    path="/full-name",
    endpoint=change_full_name_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Change user pin endpoint.",
)
