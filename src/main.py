from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import OAuthFlowPassword, OAuthFlows
from src.auth.routers import health_check
from src.database.connection import database_connection
from src.database.models import async_main
from starlette.middleware.sessions import SessionMiddleware
from src.secret import MIDDLEWARE_SECRET_KEY
from src.auth.routers.send_otp import save_phone_number
from src.auth.routers.google_sso import (
    authentication,
    login,
)
from src.auth.routers.monthly_schemas import (
    create_schema,
    list_schema,
    delete_category_schema,
    update_category_schema,
)
from src.auth.routers.monthly_spends import (
    create_spend,
    list_spend,
    update_monthly_spend,
    delete_monthly_spend,
)
from src.auth.routers.users import (
    create_pin,
    detail,
    get_user_login,
    logout,
    register,
    get_user_forgot_pin,
    send_reset_link,
)
from src.auth.routers.authorizations import access_token, refresh_token
from src.auth.routers.account_verification import verify_phone_number

app = FastAPI(
    root_path="/api/v1",
    title="FastAPI Backend Application",
    description="Backend application for finance-tracker.",
    version="1.0",
)
app.openapi_scheme = {
    "type": "oauth2",
    "flows": OAuthFlows(password=OAuthFlowPassword(tokenUrl="auth/token")),
}


@app.on_event("startup")
async def startup():
    await async_main()


@app.on_event("shutdown")
async def shutdown():
    await database_connection().dispose()


app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_check.router)
app.include_router(create_schema.router)
app.include_router(update_category_schema.router)
app.include_router(delete_category_schema.router)
app.include_router(list_schema.router)
app.include_router(create_spend.router)
app.include_router(list_spend.router)
app.include_router(update_monthly_spend.router)
app.include_router(delete_monthly_spend.router)
app.include_router(access_token.router)
app.include_router(refresh_token.router)
app.include_router(logout.router)
app.include_router(detail.router)
app.include_router(get_user_login.router)
app.include_router(register.router)
app.include_router(create_pin.router)
app.include_router(get_user_forgot_pin.router)
app.include_router(send_reset_link.router)
app.include_router(login.router)
app.include_router(authentication.router)
app.include_router(save_phone_number.router)
app.include_router(verify_phone_number.router)
