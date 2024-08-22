from typing import Annotated
from src.auth.schema.response import ResponseDefault
from src.auth.utils.request_format import AddEmail
from src.auth.utils.jwt.general import get_current_user
from fastapi import APIRouter, status, Depends, HTTPException
from src.auth.utils.database.general import is_using_registered_email, update_user_email

router = APIRouter(tags=["account-verification"], prefix="/add")


async def add_email_endpoint(
    schema: AddEmail,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ResponseDefault:
    response = ResponseDefault()
    registered_email = await is_using_registered_email(email=schema.email)

    try:
        if current_user.verified_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User already have an verified email.",
            )

        if current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User already have an email.",
            )

        if registered_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered. Please use another email.",
            )

        await update_user_email(user_uuid=current_user.user_uuid, email=schema.email)

        response.success = True
        response.message = "Success add new email."

    except HTTPException as E:
        raise E

    except Exception:
        pass

    return response


router.add_api_route(
    methods=["PATCH"],
    path="/email",
    response_model=ResponseDefault,
    endpoint=add_email_endpoint,
    status_code=status.HTTP_201_CREATED,
    summary="Add email to current validated user.",
)
