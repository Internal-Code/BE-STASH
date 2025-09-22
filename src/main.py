from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.secret import MIDDLEWARE_SECRET_KEY
from errors.register_error import register_exception_handlers
from starlette.middleware.sessions import SessionMiddleware
from src.common.routers import health, search_countries

app = FastAPI(
    root_path="/api/v1",
    title="STASH Backend Application",
    description="Backend application for STASH.",
    version="0.1",
)

register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_SECRET_KEY)
app.include_router(health.router)
app.include_router(search_countries.router)
