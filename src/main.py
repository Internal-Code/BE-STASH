from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from src.routers import health_check
from services.postgres.models import database_migration
from src.secret import Config
from fastapi.middleware.cors import CORSMiddleware
from services.postgres.connection import database_connection
from utils.custom_error import create_exception_handler
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.models import OAuthFlowPassword, OAuthFlows
from utils.custom_error import (
    AuthenticationFailed,
    EntityAlreadyExistError,
    EntityDoesNotExistError,
    EntityAlreadyVerifiedError,
    ServiceError,
    InvalidOperationError,
    InvalidTokenError,
    EntityAlreadyAddedError,
    EntityForceInputSameDataError,
    DatabaseError,
    EntityDoesNotMatchedError,
    MandatoryInputError,
    EntityAlreadyFilledError,
)
from src.routers.user_send_otp import send_otp_phone_number, send_otp_email
from src.routers.user_reset_account import user_send_reset_link, user_reset_pin
from src.routers.monthly_schema import (
    create_schema,
    list_schema,
    delete_category_schema,
    update_category_schema,
)
from src.routers.monthly_spend import (
    create_spend,
    list_spend,
    update_monthly_spend,
    delete_monthly_spend,
)
from src.routers.user_general import (
    user_login,
    user_generate_refresh_token,
    get_user,
    user_logout,
)
from src.routers.user_register import (
    user_create_pin,
    user_wrong_phone_number,
    user_new_accrount,
    sso_authentication,
    sso_login,
)
from src.routers.user_detail import (
    user_detail_phone_number,
    user_detail_email,
    user_detail_full_name,
    user_add_email,
)
from src.routers.user_verification import (
    verify_phone_number,
    verify_email,
)
from src.routers.user_update_account import (
    change_verified_email,
    change_phone_number,
    change_pin,
    change_full_name,
)

config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database_migration()
    yield
    await database_connection().dispose()


app = FastAPI(
    root_path="/api/v1",
    title="STASH Backend Application",
    description="Backend application for STASH.",
    version="1.0.0",
    lifespan=lifespan,
)

app.openapi_scheme = {
    "type": "oauth2",
    "flows": OAuthFlows(password=OAuthFlowPassword(tokenUrl="auth/token")),
}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=config.MIDDLEWARE_SECRET_KEY)


app.include_router(health_check.router)
app.include_router(create_schema.router)
app.include_router(update_category_schema.router)
app.include_router(delete_category_schema.router)
app.include_router(list_schema.router)
app.include_router(create_spend.router)
app.include_router(list_spend.router)
app.include_router(update_monthly_spend.router)
app.include_router(delete_monthly_spend.router)
app.include_router(user_login.router)
app.include_router(user_generate_refresh_token.router)
app.include_router(user_logout.router)
app.include_router(user_detail_full_name.router)
app.include_router(get_user.router)
app.include_router(user_new_accrount.router)
app.include_router(user_create_pin.router)
app.include_router(user_send_reset_link.router)
app.include_router(sso_login.router)
app.include_router(sso_authentication.router)
app.include_router(send_otp_phone_number.router)
app.include_router(verify_phone_number.router)
app.include_router(verify_email.router)
app.include_router(user_wrong_phone_number.router)
app.include_router(user_reset_pin.router)
app.include_router(send_otp_email.router)
app.include_router(user_add_email.router)
app.include_router(change_verified_email.router)
app.include_router(change_phone_number.router)
app.include_router(user_detail_phone_number.router)
app.include_router(user_detail_email.router)
app.include_router(change_pin.router)
app.include_router(change_full_name.router)


app.add_exception_handler(
    exc_class_or_status_code=InvalidOperationError,
    handler=create_exception_handler(
        status.HTTP_400_BAD_REQUEST, "Can't perform the operation."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=AuthenticationFailed,
    handler=create_exception_handler(
        status.HTTP_401_UNAUTHORIZED,
        "Authentication failed due to invalid credentials.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityDoesNotExistError,
    handler=create_exception_handler(
        status.HTTP_404_NOT_FOUND, "Entity does not exist."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityAlreadyFilledError,
    handler=create_exception_handler(
        status.HTTP_403_FORBIDDEN, "Entity already filled."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityDoesNotMatchedError,
    handler=create_exception_handler(
        status.HTTP_400_BAD_REQUEST,
        "User input data that does not matched on saved data on database.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityAlreadyExistError,
    handler=create_exception_handler(
        status.HTTP_409_CONFLICT,
        "Entity already saved.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityAlreadyVerifiedError,
    handler=create_exception_handler(
        status.HTTP_403_FORBIDDEN,
        "Entity already verified.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityForceInputSameDataError,
    handler=create_exception_handler(
        status.HTTP_403_FORBIDDEN,
        "Cannot use same data.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=EntityAlreadyAddedError,
    handler=create_exception_handler(
        status.HTTP_403_FORBIDDEN,
        "Entity already have data.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=InvalidTokenError,
    handler=create_exception_handler(
        status.HTTP_401_UNAUTHORIZED, "Invalid token, please re-authenticate again."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=ServiceError,
    handler=create_exception_handler(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "A service seems to be down, try again later.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=DatabaseError,
    handler=create_exception_handler(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Database error.",
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=MandatoryInputError,
    handler=create_exception_handler(
        status.HTTP_403_FORBIDDEN,
        "User not inputed mandatory data yet.",
    ),
)
