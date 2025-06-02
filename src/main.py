from fastapi import FastAPI
from src.routers import health_check
from src.secret import MIDDLEWARE_SECRET_KEY
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from services.postgre.model import database_migration
from services.postgre.connection import database_connection
from services.postgre.handler import migrate_country
from starlette.middleware.sessions import SessionMiddleware
from utils.exception_handler import register_exception_handlers
from fastapi.openapi.models import OAuthFlowPassword, OAuthFlows
from src.routers.user_management import register_user, get_country
# from src.routers.user_register import register_user, create_pin
# from src.routers.user_wrong_account import wrong_email, wrong_phone_number
# from src.routers.user_send_otp import send_otp_phone_number, send_otp_email
# from src.routers.user_verification import verify_phone_number, verify_email
# from src.routers.user_register.sso.google import sso_authentication, sso_login
# from src.routers.user_reset_account import reset_pin, send_reset_link, forget_user
# from src.routers.user_general import login, logout, get_user, refresh_token
# from src.routers.user_update_account import (
#     update_full_name,
#     update_phone_number,
#     update_pin,
#     update_email,
# )
# from src.routers.monthly_spend import (
#     create_spend,
#     detail_spend,
#     delete_spend,
#     update_description,
#     update_amount,
# )
# from src.routers.monthly_category import (
#     create_category,
#     delete_category,
#     update_category,
#     update_budget,
# )
# from src.routers.user_detail import (
#     add_email,
#     detail_email,
#     detail_full_name,
#     detail_phone_number,
# )
# from src.routers.monthly_schema import (
#     create_schema,
#     delete_schema,
#     update_schema,
#     list_schema,
#     detail_schema,
# )


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await database_migration()
        await migrate_country()
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
app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_SECRET_KEY)

app.include_router(health_check.router)
app.include_router(register_user.router)
app.include_router(get_country.router)
# app.include_router(delete_schema.router)
# app.include_router(list_schema.router)
# app.include_router(update_schema.router)
# app.include_router(detail_schema.router)
# app.include_router(delete_spend.router)
# app.include_router(create_category.router)
# app.include_router(delete_category.router)
# app.include_router(update_category.router)
# app.include_router(update_budget.router)
# app.include_router(update_description.router)
# app.include_router(update_amount.router)
# app.include_router(create_spend.router)
# app.include_router(detail_spend.router)
# app.include_router(add_email.router)
# app.include_router(detail_email.router)
# app.include_router(detail_full_name.router)
# app.include_router(detail_phone_number.router)
# app.include_router(get_user.router)
# app.include_router(refresh_token.router)
# app.include_router(login.router)
# app.include_router(logout.router)
# app.include_router(register_user.router)
# app.include_router(sso_authentication.router)
# app.include_router(sso_login.router)
# app.include_router(create_pin.router)
# app.include_router(forget_user.router)
# app.include_router(reset_pin.router)
# app.include_router(send_reset_link.router)
# app.include_router(send_otp_email.router)
# app.include_router(send_otp_phone_number.router)
# app.include_router(update_email.router)
# app.include_router(update_full_name.router)
# app.include_router(update_phone_number.router)
# app.include_router(update_pin.router)
# app.include_router(verify_phone_number.router)
# app.include_router(verify_email.router)
# app.include_router(wrong_phone_number.router)
# app.include_router(wrong_email.router)
