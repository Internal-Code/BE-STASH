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
    initialization,
    createSchema,
    updateCategorySchema,
    deleteCategorySchema,
    getSchema
)

app = FastAPI(
    # TODO: implement server migration, prepare for stagging and production
    # servers=[
    #     {"url": "https://stag.example.com", "description": "Staging environment"},
    #     {"url": "https://prod.example.com", "description": "Production environment"},
    # ],
    root_path="/api/v1"
)

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

app.include_router(initialization.router)
app.include_router(createSchema.router)
app.include_router(updateCategorySchema.router)
app.include_router(deleteCategorySchema.router)
app.include_router(getSchema.router)