from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowPassword
from src.auth.routers import health_check
from src.database.connection import database_connection
from src.database.models import async_main
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
from src.auth.routers.account_managements import access_token, refresh_token

from src.auth.routers.users import register_account, detail_account

app = FastAPI(root_path="/api/v1")
app.openapi_scheme = {
    "type": "oauth2",
    "flows": OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl="auth/token")),
}


@app.on_event("startup")
async def startup():
    await async_main()


@app.on_event("shutdown")
async def shutdown():
    await database_connection().dispose()


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
app.include_router(register_account.router)
app.include_router(access_token.router)
app.include_router(detail_account.router)
app.include_router(refresh_token.router)
