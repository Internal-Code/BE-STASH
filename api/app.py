from fastapi import FastAPI
from api.utils.database import general
from fastapi.middleware.cors import CORSMiddleware
from api.database.databaseModel import async_main
from api.database.databaseConnection import database_connection
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from api.database import (
    databaseConnection,
    databaseModel
)
from api.routes import (
    databaseInsert,
    initialization
)

app = FastAPI()

#TODO: Refactor remap documentation given by FastAPI
@app.on_event("startup")
async def startup():
    await async_main()

@app.on_event("shutdown")
async def shutdown():
    await database_connection().dispose()

@app.get("/api/v1/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get("/api/v1/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@next/bundles/redoc.standalone.js",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(initialization.router)
app.include_router(databaseInsert.router)