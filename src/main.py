from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import health_check
from src.secret import MIDDLEWARE_SECRET_KEY
from errors.register_error import register_exception_handlers
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI(
    root_path="/api/v1",
    title="STASH Backend Application",
    description="Backend application for STASH.",
    version="0.01",
)

register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_SECRET_KEY)
app.include_router(health_check.router)
