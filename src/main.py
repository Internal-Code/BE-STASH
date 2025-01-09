from src.secret import Config
from utils.exception_handler import register_exception_handlers
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from services.postgres.models import database_migration
from services.postgres.connection import database_connection
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.models import OAuthFlowPassword, OAuthFlows
from src.routers import health_check
from src.routers.user_send_otp import send_otp_phone_number
from src.routers.user_verification import verify_phone_number
from src.routers.user_general import user_login
from src.routers.user_general import get_user
from src.routers.user_update_account import change_full_name, change_phone_number
from src.routers.user_register import user_new_account, user_create_pin, user_wrong_phone_number
from src.routers.user_detail import user_detail_full_name, user_detail_email, user_detail_phone_number, user_add_email
from src.routers.monthly_schema import (
    create_category,
    create_schema,
    list_schema,
    list_category,
    delete_category,
    delete_schema,
    update_schema,
    update_category,
)

config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await database_migration()
        yield
    finally:
        await database_connection().dispose()


app = FastAPI(
    root_path="/api/v1",
    title="STASH Backend Application",
    description="Backend application for STASH.",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app=app)

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
app.include_router(list_schema.router)
app.include_router(update_schema.router)
app.include_router(delete_schema.router)
app.include_router(create_category.router)
app.include_router(list_category.router)
app.include_router(update_category.router)
app.include_router(delete_category.router)
# app.include_router(update_category_schema.router)
# app.include_router(delete_category_schema.router)
# app.include_router(list_schema.router)
# app.include_router(create_spend.router)
# app.include_router(list_spend.router)
# app.include_router(update_monthly_spend.router)
# app.include_router(delete_monthly_spend.router)
app.include_router(user_login.router)
# app.include_router(user_generate_refresh_token.router)
# app.include_router(user_logout.router)
app.include_router(user_detail_full_name.router)
app.include_router(get_user.router)
app.include_router(user_new_account.router)
app.include_router(user_create_pin.router)
# app.include_router(user_send_reset_link.router)
# app.include_router(sso_login.router)
# app.include_router(sso_authentication.router)
app.include_router(send_otp_phone_number.router)
app.include_router(verify_phone_number.router)
# app.include_router(verify_email.router)
app.include_router(user_wrong_phone_number.router)
# app.include_router(user_reset_pin.router)
# app.include_router(send_otp_email.router)
app.include_router(user_add_email.router)
# app.include_router(change_verified_email.router)
app.include_router(change_phone_number.router)
app.include_router(user_detail_phone_number.router)
app.include_router(user_detail_email.router)
# app.include_router(change_pin.router)
app.include_router(change_full_name.router)
